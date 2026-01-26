# app/services/classifier.py
"""
Klasifikasi dokumen: surat_masuk vs surat_keluar.
Support ML model (jika tersedia) atau fallback ke rule-based.
"""

import logging
import re
from typing import Tuple
from pathlib import Path

log = logging.getLogger(__name__)

# Try to load ML model if available
ML_MODEL = None
try:
    import joblib
    model_path = Path(__file__).parent.parent.parent / "data" / "classifier_model.pkl"
    if model_path.exists():
        ML_MODEL = joblib.load(model_path)
        log.info(f"✅ ML classifier loaded from {model_path}")
except Exception as e:
    log.warning(f"⚠️  ML model not available, using rule-based: {e}")

# ============================================================================
# LOGIKA BARU: Cek surat keluar dulu, sisanya masuk/lainnya
# ============================================================================

# Ciri KHAS Surat Keluar (dari Kelurahan ke pihak lain)
SURAT_KELUAR_INDICATORS = [
    # Header surat keluar
    r"kepada\s+yth\.?",
    r"kepada\s+yang\s+terhormat",
    r"yth\.?\s+(bapak|ibu|saudara)",
    
    # Lokasi penerima
    r"di\s+tempat",
    r"di\s+-\s+",  # "Di - Jakarta" 
    
    # Closing surat keluar
    r"demikian\s+(kami\s+)?sampaikan",
    r"atas\s+perhatian(nya)?\s+(kami\s+)?ucapkan",
    r"hormat\s+kami",
    
    # TTD dari pejabat kelurahan
    r"(lurah|camat|kepala\s+seksi|kasi)\s+pela\s+mampang",
    r"(an\.\s+)?(lurah|camat)",
    
    # Kop surat kelurahan (pengirim)
    r"pemerintah\s+(provinsi|kota).*kelurahan\s+pela\s+mampang",
    r"kelurahan\s+pela\s+mampang.*kecamatan\s+mampang\s+prapatan",
    
    # Jenis surat keluar
    r"surat\s+keputusan",
    r"surat\s+perintah",
    r"surat\s+tugas",
    r"surat\s+keterangan",
    r"surat\s+edaran",
]

# Ciri umum SURAT (punya nomor, perihal, dll)
SURAT_INDICATORS = [
    r"no(mor)?\.?\s*[:.]?\s*\d+",  # Nomor surat
    r"\d+/\w+/\w+/\d+",            # Format nomor 123/SK/KEL/2026
    r"perihal\s*:",
    r"hal\s*:",
    r"lampiran\s*:",
    r"surat\s+(masuk|keluar|undangan|permohonan)",
    r"(kepada|dari)\s+(yth|yang terhormat)",
    r"dengan\s+hormat",
]


def classify_ml(text: str) -> Tuple[str, float]:
    """
    Classify using ML model with fallback to rules for low confidence.
    Returns: (jenis, confidence)
    """
    try:
        prediction = ML_MODEL.predict([text])[0]
        proba = ML_MODEL.predict_proba([text])[0]
        confidence = max(proba)
        
        # Convert to our format
        jenis = "keluar" if prediction == "keluar" else "masuk"
        
        # If ML confidence is low (<70%), fallback to rule-based
        if confidence < 0.70:
            log.info(f"⚠️ ML confidence low ({confidence:.2f}), fallback to rules")
            return classify_rules(text)
        
        log.info(f"✅ ML prediction: {jenis} (confidence: {confidence:.2f})")
        return jenis, float(confidence)
    except Exception as e:
        log.error(f"ML classification error: {e}")
        return classify_rules(text)


def classify_rules(text: str) -> Tuple[str, float]:
    """
    Rule-based classification dengan logika baru:
    1. Cek apakah ini SURAT KELUAR (ciri khas jelas)
    2. Kalau bukan keluar, cek apakah ini SURAT (punya nomor/perihal/dll)
       - Kalau ya → MASUK (default untuk surat yang bukan keluar)
       - Kalau tidak → LAINNYA (bukan surat)
    
    Returns: (jenis, confidence)
    """
    t = text.lower()
    
    # STEP 1: Cek indikator SURAT KELUAR
    keluar_count = 0
    for pattern in SURAT_KELUAR_INDICATORS:
        if re.search(pattern, t, re.IGNORECASE):
            keluar_count += 1
    
    # STEP 2: Cek apakah ini SURAT (punya atribut surat)
    surat_count = 0
    for pattern in SURAT_INDICATORS:
        if re.search(pattern, t, re.IGNORECASE):
            surat_count += 1
    
    # DECISION LOGIC
    # Threshold: 3+ indikator keluar → confidently KELUAR
    if keluar_count >= 3:
        confidence = min(0.95, 0.6 + (keluar_count * 0.1))
        log.info(f"✅ SURAT KELUAR detected (indicators: {keluar_count})")
        return "keluar", confidence
    
    # Punya ciri surat tapi bukan keluar → MASUK
    # Threshold diturunkan jadi 1+ (lebih fleksibel)
    if surat_count >= 1:
        confidence = min(0.90, 0.55 + (surat_count * 0.1))
        log.info(f"✅ SURAT MASUK detected (surat indicators: {surat_count}, keluar indicators: {keluar_count})")
        # Warn if confidence is low
        if confidence < 0.70:
            log.warning(f"⚠️ Low confidence classification ({confidence:.2f}) - review may be needed")
        return "masuk", confidence
    
    # Tidak punya ciri surat yang jelas → LAINNYA (dokumen umum)
    log.warning(f"⚠️ DOKUMEN LAIN detected (surat indicators: {surat_count}, keluar indicators: {keluar_count}) - low indicators")
    return "lainnya", 0.65



def classify(text: str) -> Tuple[str, float]:
    """
    Main classification function.
    Uses ML model if available, otherwise falls back to rules.
    
    Returns:
        (jenis, confidence) where jenis is 'masuk', 'keluar', or 'lainnya'
    """
    if ML_MODEL is not None:
        return classify_ml(text)
    else:
        return classify_rules(text)
