
# app/services/metadata.py
"""
Ekstraksi metadata (nomor surat, perihal, tanggal, pengirim/penerima, tahun, jenis).
Disesuaikan untuk pola surat Kelurahan DKI:
- Nomor contoh: 655-HM.03.04 (OCR bisa memberi '/-' -> dibersihkan).
- Label umum: Nomor, Sifat, Lampiran, Hal/Perihal.
- Tanggal format Indonesia: 12 Desember 2025.
- Jenis: 'masuk' vs 'keluar' - uses ML classifier if available, otherwise heuristics.
"""

import logging
import re
from datetime import datetime
from typing import Dict, Optional, Tuple, List

log = logging.getLogger(__name__)

# Try to import ML classifier
try:
    from app.services.classifier_ml import classify as ml_classify
    USE_ML_CLASSIFIER = True
    log.info("✅ ML Classifier available for metadata extraction")
except ImportError:
    USE_ML_CLASSIFIER = False
    log.info("ℹ️  Using rule-based classification (ML classifier not available)")

BULAN_ID = {
    'januari': 1, 'februari': 2, 'maret': 3, 'april': 4, 'mei': 5, 'juni': 6,
    'juli': 7, 'agustus': 8, 'september': 9, 'oktober': 10, 'november': 11, 'desember': 12
}

HEADER_KEYWORDS = (
    "PEMERINTAH",
    "DINAS",
    "KELURAHAN",
    "KECAMATAN",
    "KOTA",
    "KEMENTERIAN",
    "BADAN",
    "DEWAN",
    "SEKRETARIAT",
    "PT",
    "CV",
    "YAYASAN",
)

SIGNER_ROLE_KEYWORDS = (
    "KEPALA",
    "PLT",
    "PLH",
    "LURAH",
    "CAMAT",
    "KETUA",
    "DIREKTUR",
    "MANAGER",
    "SEKRETARIS",
)

LABEL_ALIASES = {
    "nomor": ("nomor", "no", "nomer", "nemor"),
    "perihal": ("perihal", "hal"),
    "lampiran": ("lampiran",),
    "sifat": ("sifat",),
}


def _clean_text(text: str) -> str:
    """Clean OCR noise and normalize spacing efficiently."""
    if not text:
        return ""
    
    # Fast OCR error fixes (chained replacements more efficient than multiple calls)
    replacements = [
        ("/-", "-"), ("I/", "/"), ("|/", "/"), ("\\ /", ""),
        ("OS '/", "05 /"), ("OB '/", "08 /"), ("OI '/", "01 /"), ("O5 '/", "05 /")
    ]
    t = text
    for old, new in replacements:
        t = t.replace(old, new)
    
    # Pattern-based fixes (regex operations)
    t = re.sub(r'(\d)\\\s*/', r'\1/', t)  # digit\space/slash → digit/
    t = re.sub(r"(\d{2,3})\s*'\s*/", r"\1 /", t)  # Remove apostrophe artifacts
    
    # Contextual O→0 and l→1 ONLY in number patterns (preserve text content)
    def fix_nomor(match):
        return match.group(0).replace("O", "0").replace("l", "1")
    
    # Match surat number patterns (e.g., 451/KS.O2.OO, B-123/PEM/2025)
    t = re.sub(r'\b[A-Z0-9Ol]{1,8}[\-\/\.][A-Z0-9Ol\.\-\/]{2,}\b', fix_nomor, t, flags=re.IGNORECASE)
    
    # Normalize whitespace
    t = re.sub(r"[ \t]+", " ", t)  # Multiple spaces/tabs -> single space
    t = re.sub(r"\n\s*\n\s*\n+", "\n\n", t)  # Multiple blank lines -> double newline
    
    return t.strip()


def _normalize_line(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    cleaned = re.sub(r"\s+", " ", value).strip(" :-")
    if not cleaned:
        return None
    if cleaned.isupper():
        return cleaned.title()
    return cleaned


def _is_label_line(line: str) -> Optional[str]:
    """Check if line contains a known label (with or without value after colon)."""
    # Extract label part (before colon if present)
    if ":" in line:
        label_part = line.split(":", 1)[0]
    else:
        label_part = line
    
    lowered = label_part.lower().strip(" :.-")
    
    for key, aliases in LABEL_ALIASES.items():
        if lowered in aliases:
            return key
    
    return None


def _find_label_value(lines: List[str], idx: int, label_key: Optional[str] = None) -> Optional[str]:
    """Extract value after label, supporting multi-line values for perihal."""
    current = lines[idx]
    
    # Priority 1: Value on SAME line after colon
    # Pattern: "Nomor    : 451/KS.02.00" or "No :  451/KS.02.00"
    # Look for colon in current line
    if ":" in current:
        # Split by colon and take everything after it
        parts = current.split(":", 1)
        if len(parts) == 2:
            value = parts[1].strip()
            
            # For perihal: collect multi-line content (join continuation lines)
            if label_key == "perihal" and value:
                collected_lines = [value]
                # Look ahead for continuation (non-label lines)
                for offset in range(1, 5):  # Check next 4 lines
                    next_idx = idx + offset
                    if next_idx >= len(lines):
                        break
                    next_line = lines[next_idx].strip()
                    if not next_line:
                        break  # Empty line = end of perihal
                    if _is_label_line(next_line):
                        break  # Next label found = end of perihal
                    # Check if line looks like start of new section (Kepada, Yth)
                    if re.match(r"(?i)^(kepada|yth|dengan|sehubungan)", next_line):
                        break
                    collected_lines.append(next_line)
                
                # Join collected lines
                full_value = " ".join(collected_lines)
                return _filtered_label_value(_normalize_line(full_value), label_key)
            
            # For nomor, take only first token (before space)
            if label_key == "nomor" and value:
                first_token = value.split()[0] if value.split() else value
                filtered = _filtered_label_value(first_token, label_key)
                if filtered:
                    return filtered
            elif value:
                return _filtered_label_value(_normalize_line(value), label_key)
    
    # Priority 2: Label without colon, value on next line
    # "Nomor" on one line, "451/KS.02.00" on next line
    for offset in range(1, 3):
        j = idx + offset
        if j >= len(lines):
            break
        candidate = lines[j].strip()
        if not candidate:
            continue
        # Skip if next line is another label
        if _is_label_line(candidate):
            break
        # Check if line starts with colon (continuation)
        if candidate.startswith(":"):
            value = candidate[1:].strip()
            
            # For perihal: collect multi-line
            if label_key == "perihal" and value:
                collected_lines = [value]
                for offset2 in range(1, 5):
                    next_idx = j + offset2
                    if next_idx >= len(lines):
                        break
                    next_line = lines[next_idx].strip()
                    if not next_line or _is_label_line(next_line):
                        break
                    if re.match(r"(?i)^(kepada|yth|dengan|sehubungan)", next_line):
                        break
                    collected_lines.append(next_line)
                full_value = " ".join(collected_lines)
                return _filtered_label_value(_normalize_line(full_value), label_key)
            
            if label_key == "nomor" and value:
                first_token = value.split()[0] if value.split() else value
                return _filtered_label_value(first_token, label_key)
            return _filtered_label_value(_normalize_line(value), label_key)
        # Otherwise take the whole line as value
        return _filtered_label_value(_normalize_line(candidate), label_key)

    return None


def _filtered_label_value(value: Optional[str], label_key: Optional[str]) -> Optional[str]:
    """Filter dan validate extracted value berdasarkan label type.
    
    PERBAIKAN: Blacklist hanya reject jika SELURUH value adalah blacklist word,
    tidak reject jika hanya mengandung kata tersebut (untuk handle multi-token nomor).
    """
    if not value:
        return None
    
    if label_key == "nomor":
        # Blacklist: kata-kata umum yang BUKAN nomor surat
        blacklist_words = [
            "sifat", "biasa", "penting", "segera", "rahasia", 
            "lampiran", "hal", "perihal", "kepada", "yth",
            "tanggal", "tembusan", "dari"
        ]
        value_lower = value.lower().strip()
        
        # Reject ONLY if the entire value is a blacklist word (not just contains)
        if value_lower in blacklist_words:
            log.debug(f"Nomor rejected (exact blacklist match): '{value}'")
            return None
        
        # Nomor surat MUST have: digit + separator (/ or -) + more chars
        # Pattern: 451/KS.02.00, 655-HM.03.04, 123/SK/2025
        if not re.search(r"\d+[/\-][A-Za-z0-9]", value):
            log.debug(f"Nomor rejected (no pattern): '{value}'")
            return None
        
        # Additional validation: must start with digit
        if not re.match(r"^\d", value):
            log.debug(f"Nomor rejected (not start with digit): '{value}'")
            return None
        
        log.debug(f"Nomor accepted: '{value}'")
    
    return value


def extract_label_block_values(text: str) -> Dict[str, str]:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    values: Dict[str, str] = {}
    for idx, line in enumerate(lines):
        label_key = _is_label_line(line)
        if not label_key:
            continue
        value = _find_label_value(lines, idx, label_key)
        if value:
            values[label_key] = value
    return values


def _has_role_keyword(value: Optional[str]) -> bool:
    if not value:
        return False
    upper = value.upper()
    return any(keyword in upper for keyword in SIGNER_ROLE_KEYWORDS)


def extract_header_instansi(text: str) -> Optional[str]:
    cleaned = _clean_text(text)
    lines = [ln.strip() for ln in cleaned.splitlines() if ln.strip()]
    header_chunk: list[str] = []
    for line in lines[:20]:
        upper = line.upper()
        if any(keyword in upper for keyword in HEADER_KEYWORDS):
            header_chunk.append(line)
        elif header_chunk:
            break
    if header_chunk:
        joined = re.sub(r"\s{2,}", " ", " ".join(header_chunk)).strip()
        return joined or None
    return None


def extract_signature_info(text: str) -> Tuple[Optional[str], Optional[str]]:
    cleaned = _clean_text(text)
    lines = [ln.strip() for ln in cleaned.splitlines() if ln.strip()]
    tail = lines[-40:]
    signer_name = None
    role_line = None
    for line in reversed(tail):
        upper = line.upper()
        if re.search(r"(?i)\b(NIP|NIK|NRP)\b", upper):
            continue
        if not role_line and _has_role_keyword(line):
            role_line = line
            continue
        if not signer_name:
            candidate = line.strip("() ")
            upper_candidate = candidate.upper()
            if re.match(r"^[A-Z][A-Z '.-]{2,}$", upper_candidate):
                signer_name = candidate
        if signer_name and role_line:
            break
    return signer_name, role_line


def extract_signature_instansi_candidates(text: str, window: int = 80) -> List[str]:
    cleaned = _clean_text(text)
    lines = [ln.strip() for ln in cleaned.splitlines() if ln.strip()]
    tail = lines[-window:]
    candidates: List[str] = []
    for line in tail:
        instansi = extract_instansi_from_role(line)
        if instansi and instansi not in candidates:
            candidates.append(instansi)
    return candidates


def extract_tertuju_from_text(text: str) -> Optional[str]:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

    # Direct pattern: 'Kepada Yth. ...'
    pattern = re.compile(r"(?i)\bKepada\b\s+Yth\.?")
    for line in lines:
        if pattern.search(line):
            cleaned = pattern.split(line, maxsplit=1)[-1].strip(" :-")
            if cleaned and not _is_label_line(cleaned):
                return cleaned

    # Handle block where 'Kepada' and 'Yth.' are on separate lines
    for idx, line in enumerate(lines):
        if re.fullmatch(r"(?i)kepada", line.strip()):
            for j in range(idx + 1, min(idx + 6, len(lines))):
                candidate = lines[j]
                if not candidate:
                    continue
                if _is_label_line(candidate):
                    break
                # Clean up 'Yth.' prefix
                if candidate.lower().startswith("yth"):
                    cleaned = re.sub(r"(?i)^yth\.?\s*", "", candidate).strip(" :-")
                    if cleaned and len(cleaned) > 2:
                        return cleaned
                # If no Yth prefix but has meaningful content after Kepada
                elif len(candidate) > 2:
                    return candidate

    # Fallback: look for label block value for 'Kepada'
    T = _clean_text(text)
    kepada_match = re.search(r"(?i)\bKepada\b\s*[:=]?\s*(.+)", T)
    if kepada_match:
        remainder = kepada_match.group(1).strip()
        # Remove Yth prefix if present
        remainder = re.sub(r"(?i)^Yth\.?\s*", "", remainder).strip()
        # Take first line
        first = remainder.split('\n')[0].strip(" :-")
        if first and len(first) > 2 and not _is_label_line(first):
            return first

    # Fallback: Extract Yth. dari baris yang berisi Hal/Perihal
    # Pattern: "Hal : ... Yth. Ketua RW 001-014"
    for line in lines:
        # Cari pattern "Yth." di line yang mungkin juga berisi Hal/Perihal
        if re.search(r"(?i)\bYth\.?\b", line):
            # Split di Yth. dan ambil bagian setelahnya
            parts = re.split(r"(?i)\bYth\.?\s*", line)
            if len(parts) > 1:
                # Ambil bagian setelah Yth.
                after_yth = parts[-1].strip(" :-")
                # Bersihkan dari label words (Hal, Perihal, etc)
                after_yth = re.sub(r"(?i)^(Hal|Perihal|Imbauan|kebakaran)\b.*?(Yth\.?\s*)", "", after_yth).strip()
                if after_yth and len(after_yth) > 5:
                    # Clean ending words like 'Kelurahan ...' if followed by location
                    after_yth = re.sub(r"\s+di\s*$", "", after_yth).strip()
                    return after_yth
    
    # Last fallback: first standalone line containing 'Yth.'
    for line in lines:
        if re.search(r"(?i)\bYth\.\b", line) and not re.search(r"(?i)\b(Hal|Perihal)\b", line):
            cleaned = re.sub(r"(?i)^\s*Yth\.\s*", "", line).strip(" :-")
            if cleaned and len(cleaned) > 2:
                return cleaned
    return None


def normalize_person_name(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    cleaned = re.sub(r"[^A-Za-z .,'-]", " ", value)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if not cleaned:
        return None
    if cleaned.isupper():
        return cleaned.title()
    return cleaned

def extract_instansi_from_role(line: Optional[str]) -> Optional[str]:
    cleaned = _normalize_line(line)
    if not cleaned:
        return None
    m = re.search(r"(?i)(kepala|plt|plh|lurah|camat|ketua|direktur|manager|sekretaris)\s+(.+)", cleaned)
    if not m:
        return None
    instansi = m.group(2).strip(" .,:-")
    if not instansi:
        return None
    if instansi.isupper():
        instansi = instansi.title()
    return instansi

def resolve_pengirim(
    jenis: Optional[str],
    fallback_pengirim: Optional[str],
    instansi_hint: Optional[str],
    signer_name: Optional[str],
    role_line: Optional[str],
    signature_instansi: Optional[List[str]] = None,
) -> Optional[str]:
    if jenis == "keluar":
        return "Kelurahan Pela Mampang"

    header_instansi = _normalize_line(instansi_hint)
    role_instansi = extract_instansi_from_role(role_line)
    signer_instansi = extract_instansi_from_role(signer_name)
    fallback_instansi = extract_instansi_from_role(fallback_pengirim)
    fallback_line = _normalize_line(fallback_pengirim)
    normalized_signer = normalize_person_name(signer_name)
    signature_instansi = signature_instansi or []

    if jenis == "masuk":
        for candidate in (
            *signature_instansi,
            role_instansi,
            signer_instansi,
            header_instansi,
            fallback_instansi,
            fallback_line,
            normalized_signer,
        ):
            if candidate:
                return candidate
        if role_line:
            return _normalize_line(role_line) or role_line
        return None

    # jenis lainnya atau tidak terdeteksi
    for candidate in (
        fallback_line,
        header_instansi,
        normalized_signer,
        role_instansi,
        signer_instansi,
        *signature_instansi,
    ):
        if candidate:
            return candidate
    return fallback_pengirim or header_instansi
    

def extract_nomor_surat(text: str, filename: Optional[str] = None) -> Optional[str]:
    """
    Ekstrak nomor surat (contoh: 451/KS.02.00, 655-HM.03.04, 123/SK/2025).
    Pola: angka + tanda pemisah (/ atau -) + kode instansi/klasifikasi
    
    Returns:
        nomor surat atau None jika tidak ditemukan
    """
    # PERTAJAMAN: Pre-clean OCR error sebelum processing
    # Fix "OS '/" patterns yang common di OCR
    # CRITICAL: Normalize berbagai karakter quote ke ASCII dulu baru replace
    text_precleaned = text
    
    # Step 1: Normalize all Unicode quotes to ASCII space
    # OCR sering produce Unicode quotes: ' ' " " ` etc
    quote_map = str.maketrans({
        '\u2018': ' ',  # ' LEFT SINGLE QUOTATION MARK
        '\u2019': ' ',  # ' RIGHT SINGLE QUOTATION MARK  
        '\u201C': ' ',  # " LEFT DOUBLE QUOTATION MARK
        '\u201D': ' ',  # " RIGHT DOUBLE QUOTATION MARK
        '\u0060': ' ',  # ` GRAVE ACCENT
        '\u00B4': ' ',  # ´ ACUTE ACCENT
        '\u2032': ' ',  # ′ PRIME
    })
    text_precleaned = text_precleaned.translate(quote_map)
    
    # Step 2: Replace OCR error patterns
    text_precleaned = text_precleaned.replace("OS  /", "05 /")  # Double space after normalize
    text_precleaned = text_precleaned.replace("OB  /", "08 /")
    text_precleaned = text_precleaned.replace("OI  /", "01 /")
    text_precleaned = text_precleaned.replace("OS /", "05 /")   # Single space 
    text_precleaned = text_precleaned.replace("OB /", "08 /")
    text_precleaned = text_precleaned.replace("OI /", "01 /")
    
    T = _clean_text(text_precleaned)
    candidates = []  # Track candidates with confidence scores
    
    # Priority 1: Extract from label block (paling akurat) - HIGHEST PRIORITY
    label_values = extract_label_block_values(T)
    nomor_value = label_values.get("nomor")
    if nomor_value:
        nomor_value = re.sub(r"^[:\-\s]+", "", nomor_value).strip()
        nomor_value = nomor_value.strip(".,;: ")
        # Validate: must have digit and separator
        if len(nomor_value) > 3 and re.search(r"\d", nomor_value) and re.search(r"[/\-.]", nomor_value):
            candidates.append((nomor_value, 100))  # Highest confidence
            # PERBAIKAN: Tidak langsung return, masukkan ke candidates untuk dibandingkan
            log.debug(f"Nomor candidate from label block: '{nomor_value}' (confidence: 100)")

    # Priority 2: Direct pattern IMMEDIATELY after 'Nomor:' label (very accurate)
    # Look for pattern after Nomor/No label with proper separator
    # PERBAIKAN: Support spasi karena OCR kadang baca "/" jadi " "
    patterns = [
        # E-surat pattern: e-0031/BM.00
        r"(?i)\b(Nomor|No|Nomer|Nemor)\s*[:.]?\s*(e-\d+[/\-][A-Za-z0-9./\-]+)",
        # Standard pattern dengan / atau -
        r"(?i)\b(Nomor|No|Nomer|Nemor)\s*[:.]?\s*(\d+[/\-][A-Za-z0-9./\-]+)",
        # Pattern dengan spasi (OCR issue: "31 /PU.01.00" atau "38 /HM.04.02")
        r"(?i)\b(Nomor|No|Nomer|Nemor)\s*[:.]?\s*(\d+\s+[/\-][A-Za-z0-9./\-]+)",
        # Handle line break
        r"(?i)\b(Nomor|No)\s*\n\s*[:.]?\s*(\d+[/\-][A-Za-z0-9./\-]+)",
        # OCR error: huruf di awal jadi digit (OS → 05, OB → 08)
        r"(?i)\b(Nomor|No|Nomer)\s*[:.]?\s*([A-Z]{1,2}\s*['\\/]\s*[A-Z]{2}\.[0-9.]+)",
        # PERTAJAMAN: Pattern standalone 2-3 digit dengan kode: "05 / KB.03.00" atau "137/02/04/1/2025"
        r"\b(\d{2,3})\s*[/\-]\s*([A-Z]{2}\.[0-9.]+)\b",
    ]
    for pattern in patterns:
        m = re.search(pattern, T)
        if m:
            # Handle different group structures
            if len(m.groups()) >= 2 and m.group(2):
                nomor = m.group(2).strip().strip(".,;: ")
            elif len(m.groups()) == 2:
                # Pattern tanpa label: group 1 = digit, group 2 = code
                nomor = f"{m.group(1)}/{m.group(2)}".strip()
            else:
                nomor = m.group(1).strip().strip(".,;: ")
            
            # Clean up extra spaces: "31 /PU" -> "31/PU"
            nomor = re.sub(r'(\d+)\s+([/\-])', r'\1\2', nomor)
            if len(nomor) > 3 and not re.match(r"^\d{1,2}[-/]\d{1,2}[-/]\d{2,4}$", nomor):
                # PERBAIKAN: Tambahkan ke candidates, tidak langsung return
                candidates.append((nomor, 95))
                log.debug(f"Nomor candidate after label: '{nomor}' (confidence: 95)")

    # Priority 3: Token scan in EARLY header only (first 15 lines)
    # Lower confidence - only use if no label-based match
    lines = [l.strip() for l in T.splitlines()]
    for idx, l in enumerate(lines[:15]):  # Reduced window to avoid false positives
        if not l or _is_label_line(l):
            continue
        
        # Look for number-slash-code pattern
        tokens = l.split()
        for token in tokens:
            # Pattern: starts with digit(s), has separator, has letter+number code
            # Format examples: 451/KS.02.00, 655-HM.03.04, 123/SK/2025/XII
            if re.match(r"^\d+[/\-][A-Za-z0-9./\-]{2,}$", token):
                # Exclude dates (DD/MM/YYYY or DD-MM-YYYY)
                if not re.match(r"^\d{1,2}[-/]\d{1,2}[-/]\d{2,4}$", token):
                    # Lower confidence - only add as candidate
                    conf = 70 if idx < 8 else 60
                    candidates.append((token.strip(".,;"), conf))
        
        # PERTAJAMAN: Check for multi-token pattern "05 / KB.03.00" (tokens separated by space)
        # Pattern: digit(s) space slash space code
        pattern_match = re.search(r'(\d{2,3})\s+/\s+([A-Z]{2}\.\d{2}\.\d{2})', l)
        if pattern_match:
            nomor_candidate = f"{pattern_match.group(1)}/{pattern_match.group(2)}"
            conf = 75 if idx < 8 else 65
            candidates.append((nomor_candidate, conf))
            log.debug(f"Multi-token nomor found: '{nomor_candidate}' (confidence: {conf})")

    # Priority 4: Fallback filename (lowest confidence)
    if filename:
        name = filename.rsplit(".", 1)[0]
        # Extract first token if it looks like a nomor surat
        parts = name.split(maxsplit=1)
        if parts and re.match(r"^\d+[/\-][A-Za-z0-9./\-]+$", parts[0]):
            candidates.append((parts[0].strip(), 50))
    
    # Return highest confidence candidate
    if candidates:
        # Sort by confidence (descending)
        candidates.sort(key=lambda x: x[1], reverse=True)
        best_nomor = candidates[0][0]
        log.info(f"✅ Nomor extracted: '{best_nomor}' (confidence: {candidates[0][1]}, total candidates: {len(candidates)})")
        return best_nomor
    
    log.warning("⚠️  Nomor surat not found")
    return None


def extract_perihal(text: str, filename: Optional[str] = None) -> Optional[str]:
    """
    Perihal dari:
      - 'Hal: ...' atau 'Perihal: ...'
      - Fallback: baris yang mengandung kata kunci umum (Permohonan, Balasan, Undangan, Disposisi)
      - Fallback filename: 'KODE PERIHAL.pdf' -> ambil PERIHAL
    
    Returns:
        perihal surat atau None jika tidak ditemukan
    """
    # PERTAJAMAN: Pre-clean OCR error seperti di extract_nomor_surat
    # CRITICAL: Normalize berbagai karakter quote ke ASCII dulu baru replace
    text_precleaned = text
    
    # Step 1: Normalize all Unicode quotes to ASCII space
    quote_map = str.maketrans({
        '\u2018': ' ',  # ' LEFT SINGLE QUOTATION MARK
        '\u2019': ' ',  # ' RIGHT SINGLE QUOTATION MARK  
        '\u201C': ' ',  # " LEFT DOUBLE QUOTATION MARK
        '\u201D': ' ',  # " RIGHT DOUBLE QUOTATION MARK
        '\u0060': ' ',  # ` GRAVE ACCENT
        '\u00B4': ' ',  # ´ ACUTE ACCENT
        '\u2032': ' ',  # ′ PRIME
    })
    text_precleaned = text_precleaned.translate(quote_map)
    
    # Step 2: Replace OCR error patterns
    text_precleaned = text_precleaned.replace("OS  /", "05 /")  # Double space after normalize
    text_precleaned = text_precleaned.replace("OB  /", "08 /")
    text_precleaned = text_precleaned.replace("OI  /", "01 /")
    text_precleaned = text_precleaned.replace("OS /", "05 /")   # Single space
    text_precleaned = text_precleaned.replace("OB /", "08 /")
    text_precleaned = text_precleaned.replace("OI /", "01 /")
    
    T = _clean_text(text_precleaned)
    label_values = extract_label_block_values(T)
    perihal_value = label_values.get("perihal")

    def _sanitize_perihal(value: str) -> Optional[str]:
        """Clean perihal value dari noise dan validate.
        
        PERTAJAMAN: Reject jika value terlihat seperti nomor surat dengan OCR error.
        """
        if not value:
            return None
        
        cleaned = value.strip().lstrip(":- ")
        
        # PERTAJAMAN: Reject jika value berisi pattern nomor surat (termasuk OCR error)
        # Pattern: "OS '/ KB.03.00" atau "05 / KB.03.00 20 Januari"
        if re.search(r'\b[O0][S5IB0-9]\s*[\'\"`]?\s*/\s*[A-Z]{2}\.[0-9.]+', cleaned, re.IGNORECASE):
            log.debug(f"Perihal rejected (looks like nomor surat with OCR error): '{cleaned}'")
            return None
        if re.search(r'^\d{2,3}\s*/\s*[A-Z]{2}\.[0-9.]+\s+\d{1,2}\s+\w+\s+\d{4}', cleaned):
            log.debug(f"Perihal rejected (nomor + tanggal pattern): '{cleaned}'")
            return None
        
        # Remove trailing recipient references like 'Yth. ...' or 'Kepada'
        for pattern in [r"(?i)\bYth\.", r"(?i)\bKepada\b"]:
            split = re.split(pattern, cleaned)
            if split and len(split[0].strip()) >= 3:
                cleaned = split[0].strip(" ,.;")
                break
        
        # Remove common label words at the end
        cleaned = re.sub(r"(?i)\s+(kebakaran|di|jakarta|tanggal|nomor)\s*$", "", cleaned).strip()
        
        # REJECT if it's header/instansi text (all caps with specific keywords)
        upper = cleaned.upper()
        header_indicators = ["PEMERINTAH", "PROVINSI", "DAERAH", "KHUSUS", "IBUKOTA", 
                            "KOTA", "ADMINISTRASI", "KECAMATAN", "KELURAHAN", 
                            "DINAS", "KEMENTERIAN", "REPUBLIK"]
        
        # PERBAIKAN: Tingkatkan threshold dari 2 ke 3 header keywords
        # Perihal seperti "Permohonan dari Kelurahan Mampang" tetap valid
        header_count = sum(1 for keyword in header_indicators if keyword in upper)
        if header_count >= 3:  # Lebih lenient
            log.debug(f"Perihal rejected (header text with {header_count} keywords): '{cleaned}'")
            return None
        
        # Remove if it's just a single header keyword
        if cleaned.upper() in HEADER_KEYWORDS:
            log.debug(f"Perihal rejected (header keyword): '{cleaned}'")
            return None
        
        # Remove if too short or just numbers
        if len(cleaned) < 5 or cleaned.isdigit():
            log.debug(f"Perihal rejected (too short/numeric): '{cleaned}'")
            return None
        
        # Remove if it looks like a date
        if re.match(r"^\d{1,2}[-/\s]\w+[-/\s]\d{2,4}$", cleaned):
            log.debug(f"Perihal rejected (date format): '{cleaned}'")
            return None
        
        # Remove if all uppercase and very long (likely header/kop)
        if cleaned.isupper() and len(cleaned) > 40:
            log.debug(f"Perihal rejected (all caps header): '{cleaned}'")
            return None
        
        log.debug(f"Perihal accepted: '{cleaned}'")
        return cleaned

    # Priority 1: From label block
    if perihal_value:
        log.debug(f"Perihal candidate from label block: '{perihal_value}'")
        sanitized = _sanitize_perihal(perihal_value)
        if sanitized:
            log.info(f"✅ Perihal extracted (label block): '{sanitized}'")
            return sanitized

    # Priority 2: Label langsung 'Hal:' atau 'Perihal:' (handle line break + multi-line)
    label_match = re.search(r"(?i)\b(Hal|Perihal)\b", T)
    if label_match:
        remainder = T[label_match.end():]
        remainder = remainder.lstrip(" \t\r\n:- ")
        
        # Collect multi-line perihal content
        collected_lines = []
        for line in remainder.splitlines()[:10]:  # PERBAIKAN: Tingkatkan dari 5 ke 10 baris
            line = line.strip()
            if not line:
                # PERBAIKAN: Jangan langsung break pada empty line pertama,
                # perihal mungkin ada line break intentional
                if collected_lines:  # Only break if already collected something
                    break
                continue
            if _is_label_line(line):
                break  # Next label = end
            # Stop if reaching recipient section
            if re.match(r"(?i)^(kepada|yth|dengan|sehubungan)", line):
                break
            log.debug(f"Perihal line candidate: '{line}'")
            collected_lines.append(line)
        
        if collected_lines:
            # Join all collected lines
            full_perihal = " ".join(collected_lines)
            log.debug(f"Perihal candidate from direct label (multi-line): '{full_perihal}'")
            sanitized = _sanitize_perihal(full_perihal)
            if sanitized:
                log.info(f"✅ Perihal extracted (direct label): '{sanitized}'")
                return sanitized

    # Priority 3: Kata kunci umum (in middle section, not header/footer)
    keywords = r"(Permohonan|Balasan|Undangan|Disposisi|Pemberitahuan|Pengajuan|Laporan|Penyampaian|Permintaan)"
    lines = T.splitlines()
    # Search in middle section (lines 5-40), avoid header and footer
    for idx, l in enumerate(lines[5:40], start=5):
        if re.search(rf"(?i)\b{keywords}\b", l):
            log.debug(f"Perihal candidate from keyword: '{l.strip()}'")
            sanitized = _sanitize_perihal(l.strip())
            if sanitized and len(sanitized) > 10:  # Ensure substantial content
                log.info(f"✅ Perihal extracted (keyword scan): '{sanitized}'")
                return sanitized
    
    log.warning("⚠️  Perihal not found")

    # Priority 4: Fallback filename
    if filename:
        name = filename.rsplit(".", 1)[0]
        # Pattern: "NOMOR PERIHAL.pdf" -> extract PERIHAL
        mm = re.match(r"^\s*[A-Za-z0-9.\-\/]+\s+(.+)$", name)
        if mm:
            perihal_candidate = mm.group(1).strip()
            if len(perihal_candidate) > 3:
                log.info(f"✅ Perihal extracted (filename): '{perihal_candidate}'")
                return perihal_candidate
    
    log.warning("⚠️  Perihal not found after all strategies")
    return None


def extract_tanggal(text: str) -> Optional[datetime]:
    """
    Extract tanggal surat dari text.
    
    Format yang didukung:
    - '12 Desember 2025'
    - 'Jakarta, 12 Desember 2025'
    - '12-12-2025' atau '12/12/2025'
    - 'Tanggal: 12 Desember 2025'
    
    Fallback: hanya tahun (20xx) -> gunakan 1 Januari tahun tersebut
    """
    T = _clean_text(text)
    
    # Pattern 1: Format Indonesia lengkap '12 Desember 2025'
    m = re.search(r"(\d{1,2})\s+([A-Za-z]+)\s+(20\d{2})", T, re.IGNORECASE)
    if m:
        day = int(m.group(1))
        month_name = m.group(2).lower()
        year = int(m.group(3))
        month = BULAN_ID.get(month_name)
        if month:
            try:
                result = datetime(year, month, day)
                log.debug(f"Tanggal extracted (ID format): {result.strftime('%d %B %Y')}")
                return result
            except ValueError:
                # Invalid date, continue to next pattern
                pass
    
    # Pattern 2: Format numerik 'DD-MM-YYYY' atau 'DD/MM/YYYY'
    m = re.search(r"\b(\d{1,2})[-/](\d{1,2})[-/](20\d{2})\b", T)
    if m:
        day = int(m.group(1))
        month = int(m.group(2))
        year = int(m.group(3))
        try:
            result = datetime(year, month, day)
            log.debug(f"Tanggal extracted (numeric format): {result.strftime('%d %B %Y')}")
            return result
        except ValueError:
            # Invalid date, continue to next pattern
            pass
    
    # Pattern 3: Setelah label 'Tanggal:' atau 'Tgl:'
    m = re.search(r"(?i)\b(Tanggal|Tgl)\b\s*[:.]?\s*(\d{1,2})\s+([A-Za-z]+)\s+(20\d{2})", T)
    if m:
        day = int(m.group(2))
        month_name = m.group(3).lower()
        year = int(m.group(4))
        month = BULAN_ID.get(month_name)
        if month:
            try:
                result = datetime(year, month, day)
                log.debug(f"Tanggal extracted (after label): {result.strftime('%d %B %Y')}")
                return result
            except ValueError:
                pass
    
    # Fallback: Extract hanya tahun (20xx) -> gunakan 1 Januari
    y = re.search(r"\b(20\d{2})\b", T)
    if y:
        year = int(y.group(1))
        log.debug(f"Only year extracted: {year}, using Jan 1")
        return datetime(year, 1, 1)
    
    return None


def extract_pengirim_penerima(text: str) -> Dict[str, Optional[str]]:
    """
    Heuristik sederhana:
      - Penerima dari 'Kepada Yth ...'
      - Pengirim dari 'Dari:'/ 'Pengirim:'
    """
    T = _clean_text(text)
    pengirim = None
    penerima = extract_tertuju_from_text(text)

    m_from = re.search(r"(?i)\b(Dari|Pengirim)\b\s*:\s*(.+)", T)
    if m_from:
        pengirim = re.split(r"\n", m_from.group(2))[0].strip()

    return {"pengirim": pengirim, "penerima": penerima}


def detect_jenis(text: str, nomor: Optional[str] = None, filename: Optional[str] = None) -> Tuple[Optional[str], float, str]:
    """
    Deteksi jenis surat (masuk, keluar, atau lainnya).
    
    Logic:
    1. Check has nomor label -> if not, return "lainnya" (BEFORE ML classifier!)
    2. Try ML classifier if available (confidence > 0.7)
    3. Check kop Pela Mampang -> "keluar"
    4. Check nomor pattern (XX-YY.ZZ) -> "keluar"
    5. Check PEMERINTAH/KEMENTERIAN (non Pela Mampang) -> "masuk"
    6. Check filename hints
    7. Default -> "lainnya" (dokumen lainnya)
    
    Returns:
        (jenis, confidence, method) where:
        - jenis: "masuk", "keluar", or "lainnya"
        - confidence: float 0.0-1.0
        - method: detection method used (e.g., "kop-detection", "nomor-pattern", "ml-classifier")
    """
    # Clean text once and reuse
    T = _clean_text(text)
    lines = T.splitlines()[:30]
    header_text = " ".join(lines).upper()
    
    # Check for non-letter documents (paparan, buku panduan, presentasi)
    lainnya_keywords = ("PAPARAN", "BUKU PANDUAN", "PANDUAN", "PRESENTASI", "HANDBOOK", "GUIDE BOOK", "MANUAL", "MODUL")
    first_500 = T[:500].upper()
    
    if any(kw in first_500 for kw in lainnya_keywords):
        log.debug("Detected as LAINNYA: Non-letter document (paparan/panduan)")
        return "lainnya", 0.90, "non-letter-keywords"
    
    # Check for nomor label (formal letter indicator)
    has_nomor_label = bool(re.search(r"(?i)\b(Nomor|No)\b\s*[:=.\-]*\s*[A-Za-z0-9]", T))
    if not has_nomor_label:
        log.debug("Detected as LAINNYA: No nomor label found")
        return "lainnya", 0.85, "no-nomor-label"
    
    # PERBAIKAN: ML classifier dipindahkan ke akhir sebagai fallback
    # Rule-based checks dijalankan dulu karena lebih akurat untuk kasus Pela Mampang
    
    # Kop detection for Pela Mampang - PERBAIKAN LOGIKA
    # Check if Pela Mampang is in HEADER (top 10 lines) as SENDER kop
    # vs mentioned as RECIPIENT in body (Kepada Yth: Lurah Pela Mampang)
    
    header_first_10_lines = " ".join(lines[:10]).upper()
    kop_patterns = ("KELURAHAN PELA MAMPANG", "BANGKA X UJUNG", "PELAMAMAMPANGKELURAHAN", "718 2380", "7182380")
    has_kop_pela_mampang_top = (
        any(p in header_first_10_lines for p in kop_patterns) or
        ("PELA MAMPANG" in header_first_10_lines and "MAMPANG PRAPATAN" in header_first_10_lines)
    )

    # Check if this is a letter TO Pela Mampang (recipient, not sender)
    # Look for "Kepada Yth" + "Lurah/Kelurahan Pela Mampang" pattern
    # Use DOTALL flag to match across newlines
    is_recipient_pela_mampang = bool(
        re.search(r"(?i)(kepada|yth).{0,50}(lurah|kelurahan).{0,20}pela\s+mampang", T[:1000], re.DOTALL)
    )

    # Only classify as KELUAR if Pela Mampang is sender (kop on top) AND NOT recipient
    if has_kop_pela_mampang_top and not is_recipient_pela_mampang:
        log.debug("Detected as KELUAR: Kop Pela Mampang found as sender")
        return "keluar", 0.95, "kop-pela-mampang"
    
    # If Pela Mampang is recipient, this is MASUK
    if is_recipient_pela_mampang:
        log.debug("Detected as MASUK: Letter addressed TO Pela Mampang")
        return "masuk", 0.95, "recipient-pela-mampang"
    
    # --- Rule 2: Nomor Pattern Check (sebelum PEMERINTAH check) ---
    # Nomor format XX-YY.ZZ.WW atau XX/YY.ZZ.WW adalah surat keluar internal
    if nomor:
        # Pattern surat keluar: 30-BM.02.02, 31-LH.01.00, 136/02/04/1/2025
        if re.search(r"^\d{1,3}[-/][A-Z]{2}\.\d", nomor):  # XX-LH.01.00
            log.debug(f"Detected as KELUAR: Nomor pattern {nomor}")
            return "keluar", 0.90, "nomor-pattern-keluar"
        if re.search(r"^\d{1,3}/\d{2}/\d{2}", nomor):  # 136/02/04/1/2025
            log.debug(f"Detected as KELUAR: Nomor pattern {nomor}")
            return "keluar", 0.90, "nomor-pattern-keluar"
        # Pattern surat masuk (dari luar)
        if re.search(r"(?i)(?:^|/|[-_])SM(?:/|[-_]|$)", nomor):
            log.debug(f"Detected as MASUK: SM pattern in nomor")
            return "masuk", 0.90, "nomor-pattern-SM"
    
    # --- Rule 3: Jika ada PEMERINTAH tapi BUKAN Pela Mampang -> Masuk (dari instansi lain) ---
    # ONLY check ini jika belum detect Pela Mampang as sender
    if "PEMERINTAH" in header_text and not has_kop_pela_mampang_top:
        # Double check: pastikan ini bukan surat keluar yang OCR-nya rusak
        # Jika ada "KEPADA YTH" atau pattern surat keluar lainnya -> keluar
        if "KEPADA" in header_text and ("YTH" in header_text or "YANG TERHORMAT" in header_text):
            # But if Pela Mampang is the recipient, it's definitely MASUK
            if is_recipient_pela_mampang:
                log.debug("Detected as MASUK: Letter from PEMERINTAH to Pela Mampang")
                return "masuk", 0.95, "pemerintah-to-pela-mampang"
            log.debug("Detected as KELUAR: Has KEPADA YTH despite PEMERINTAH")
            return "keluar", 0.80, "kepada-yth-pattern"
        
        log.debug("Detected as MASUK: PEMERINTAH from other institution")
        return "masuk", 0.85, "pemerintah-header"
    
    if "KEMENTERIAN" in header_text or "DEWAN" in header_text or "PT." in header_text:
        log.debug("Detected as MASUK: External institution header")
        return "masuk", 0.85, "external-institution"

    # --- Fallback: Filename Check ---
    if filename:
        name = filename.rsplit(".", 1)[0]
        if re.search(r"(?i)(?:^|/|[-_])SM(?:/|[-_]|$)", name) or re.search(r"(?i)\bmasuk\b", name):
            log.debug(f"Detected as MASUK: Filename hint '{name}'")
            return "masuk", 0.70, "filename-hint"
        if re.search(r"(?i)(?:^|/|[-_])SK(?:/|[-_]|$)", name) or re.search(r"(?i)\bkeluar\b", name):
            log.debug(f"Detected as KELUAR: Filename hint '{name}'")
            return "keluar", 0.70, "filename-hint"
    
    # --- Fallback: Try ML classifier jika rules tidak bisa menentukan ---
    # ML classifier digunakan sebagai fallback terakhir dengan threshold tinggi
    if USE_ML_CLASSIFIER and len(text.strip()) > 50:
        try:
            jenis, confidence = ml_classify(text)
            # Hanya gunakan ML jika confidence sangat tinggi (>80%)
            if confidence > 0.80:
                log.info(f"ML Classifier fallback: {jenis} (confidence: {confidence:.2%})")
                return jenis, confidence, "ml-classifier"
            log.debug(f"ML Classifier confidence too low ({confidence:.2%}), defaulting to lainnya")
        except Exception as e:
            log.warning(f"ML classification failed: {e}")
    
    # Default: Dokumen Lainnya (tidak terdeteksi sebagai surat masuk/keluar)
    log.debug("Detected as LAINNYA: No clear pattern for masuk/keluar")
    return "lainnya", 0.60, "default-fallback"


def parse_metadata(text: str, filename: Optional[str], uploaded_at: datetime) -> Dict[str, Optional[str]]:
    """
    Parser terpadu untuk satu surat.
    
    Returns:
        Dictionary dengan metadata extracted dan extraction_stats untuk tracking kualitas
    """
    log.info(f"🔍 Starting metadata extraction for: {filename or 'unknown'}")
    log.debug(f"Text length: {len(text)} chars")
    
    # Extract all fields
    nomor = extract_nomor_surat(text, filename)
    dt = extract_tanggal(text)
    tanggal_str = dt.strftime("%d %B %Y") if dt and dt.day != 1 else (dt.strftime("%Y") if dt else None)
    tahun = dt.year if dt else None

    jenis, jenis_confidence, jenis_method = detect_jenis(text, nomor, filename)

    # Perihal hanya diekstrak untuk surat masuk/lainnya
    perihal = None
    if jenis != "keluar":
        perihal = extract_perihal(text, filename)
    
    # REMOVED: Ekstraksi pengirim/penerima dihapus - tidak diperlukan saat upload
    # instansi_hint = extract_header_instansi(text)
    # signer_name, role_line = extract_signature_info(text)
    # signature_instansi = extract_signature_instansi_candidates(text)
    # peng_pener = extract_pengirim_penerima(text)
    # pengirim = resolve_pengirim(...)
    # tertuju = extract_tertuju_from_text(text) or ...
    
    # Log extraction results
    log.info(f"✅ Extraction complete: nomor={nomor}, perihal={'[' + perihal[:30] + '...]' if perihal and len(perihal) > 30 else perihal}, jenis={jenis} (confidence: {jenis_confidence:.2f}, method: {jenis_method}), tahun={tahun}")
    
    # Calculate extraction stats (5 core fields only)
    extraction_stats = {
        "fields_extracted": sum([
            bool(nomor),
            bool(perihal) if jenis != "keluar" else False,
            bool(tanggal_str),
            bool(tahun),
            bool(jenis),
        ]),
        "total_fields": 5,  # Reduced from 7: removed pengirim & penerima
        "text_length": len(text),
        "has_header": False,  # Not extracted anymore
        "has_signature": False,  # Not extracted anymore
        "jenis_confidence": jenis_confidence,
        "jenis_method": jenis_method,
    }

    result = {
        "nomor": nomor,
        "tanggal_surat": tanggal_str,
        "tahun": tahun,
        "jenis": jenis,
        "jenis_confidence": jenis_confidence,
        "jenis_method": jenis_method,
        # REMOVED: pengirim dan penerima tidak dikembalikan
        "_extraction_stats": extraction_stats,  # Internal stats untuk debugging
    }
    if jenis != "keluar":
        result["perihal"] = perihal
    return result
