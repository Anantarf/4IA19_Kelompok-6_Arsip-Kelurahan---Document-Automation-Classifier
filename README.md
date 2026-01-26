# 4IA19_Kelompok 6_Arsip Kelurahan - Document Automation Classifier

Anggota Kelompok 6 - 4IA19:

1. Laurensius Aditya Danutama (50422805) — Project Manager
2. Ratih Rasmiati (51422391) — Designer
3. Ananta Raihan Fatih (50422202) — Programmer
4. Shalwa Rahgiant Permata Putri (51422533) — Analyst & QA
5. Nasywa Aqilla Athaya Syah (51422208) — Technical Writer

📦 **GitHub**: [https://github.com/Anantarf/4IA19_Kelompok-6_Arsip-Kelurahan---Document-Automation-Classifier](https://github.com/Anantarf/4IA19_Kelompok-6_Arsip-Kelurahan---Document-Automation-Classifier)

> ⚠️ **Note**: Sistem ini full-stack application (backend FastAPI + frontend React). GitHub Pages hanya untuk frontend statis. Untuk demo lengkap, run lokal dengan instruksi di bawah.

Sistem manajemen arsip digital untuk **Kelurahan Pela Mampang** menggunakan FastAPI + MySQL + React.

Sistem ini otomatis mengklasifikasi, mengindeks, dan menyimpan dokumen surat masuk/keluar dengan ekstraksi metadata cerdas (OCR untuk PDF scan).

> **🚀 Status**: Production-ready dengan MySQL database, rate limiting, dan monitoring tools aktif.

## ✨ Fitur Utama

- 📄 **Upload Dokumen**: DOCX & PDF dengan validasi otomatis dan preview
- 🔤 **Ekstraksi Teks**: Parser native + OCR Tesseract untuk PDF scan
- 🤖 **Klasifikasi Otomatis**: Surat masuk vs keluar (rule-based + ML ready)
- 📊 **Parsing Metadata**: Nomor surat, tanggal, perihal (regex)
- 📁 **Auto-Foldering**: Penyimpanan terstruktur per tahun/bulan/jenis
- 🏷️ **Nama File Original**: Dokumen ditampilkan dengan nama file asli saat upload
- 🔍 **Pencarian Canggih**: Hierarchical browser + global search dengan debounce
- 📥 **Preview Modal**: Full-screen document preview dengan metadata lengkap
- ✏️ **Edit Metadata**: Rename (perihal) dokumen dengan konfirmasi
- 🗑️ **Delete Management**: Hapus dokumen dengan hard delete + confirmation
- 📦 **Ekspor Data**: ZIP arsip per tahun/jenis + CSV metadata
- 🛡️ **Keamanan**: JWT authentication, role-based access control (admin/staf), rate limiting
- 👥 **Admin Users**: Kelola akun + reset password (admin-only)
- 📱 **UI Modern**: React + TypeScript + Tailwind CSS responsive design
- ⚡ **Performance**: React Query v5 caching, optimistic updates
- 🔔 **Notifications**: Toast notifications untuk semua operasi

## 📈 Status Aplikasi (Januari 2026)

✅ **Database**: Berhasil dimigrasikan ke MySQL untuk persistent storage  
✅ **Security**: Rate limiting, CORS, Trusted Host middleware aktif  
✅ **Testing**: Backend (6/6 tests pass), Frontend tests tersedia  
✅ **Data Integrity**: Konsistensi data terverifikasi, recovery tools siap pakai  
✅ **Performance**: Backend port 8001, Frontend port 5173, API responsif  
✅ **Monitoring**: Scripts untuk consistency check dan maintenance tersedia

## 🛠️ Tech Stack

### Backend

- **Framework**: FastAPI 0.115.2 (Python 3.11+)
- **Database**: MySQL 8.0+ with SQLAlchemy 2.0.25 ORM (migrated from SQLite)
- **Authentication**: JWT (HS256) with Bearer tokens (python-jose)
- **Password Hashing**: bcrypt 3.2.2 + passlib 1.7.4
- **Security**: Rate limiting (slowapi), CORS, Trusted Host middleware
- **Database Driver**: PyMySQL 1.1.0 for MySQL connectivity
- **OCR**: Tesseract + pytesseract 0.3.10
- **PDF Processing**: PyMuPDF 1.24.10, pdfminer.six 20231228
- **DOCX Processing**: python-docx 1.1.0
- **Image Processing**: Pillow 10.3.0, pdf2image 1.17.0
- **Machine Learning Ready**: scikit-learn 1.3.2, joblib 1.3.2

### Frontend

- **Framework**: React 18.3 + TypeScript 5.6
- **Build Tool**: Vite 5.4.21
- **Styling**: Tailwind CSS 3.4
- **State Management**: TanStack Query (React Query) v5 with isPending API
- **Forms**: React Hook Form + react-dropzone
- **PDF Viewer**: react-pdf (pdfjs-dist 3.12.313)
- **Icons**: Lucide React
- **HTTP Client**: Axios with JWT interceptors
- **Routing**: React Router DOM v6

### DevOps

- **Containerization**: Docker + Docker Compose
- **Web Server**: Uvicorn (ASGI)
- **CORS**: Configured for localhost development
- **Environment**: .env configuration

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 16+ (untuk frontend)
- MySQL 8.0+ (untuk database)
- (Optional) Tesseract-OCR untuk OCR support

### Cara Tercepat (Windows)

```bash
# Clone repository
git clone https://github.com/Anantarf/4IA19_Kelompok-6_Arsip-Kelurahan---Document-Automation-Classifier.git
cd 4IA19_Kelompok-6_Arsip-Kelurahan---Document-Automation-Classifier

# Setup .env file
cp .env.example .env
# Edit .env jika perlu (SECRET_KEY, MySQL config, TESSERACT_CMD, dll)

# Untuk MySQL, pastikan konfigurasi berikut di .env:
# MYSQL_USE=1
# MYSQL_HOST=localhost
# MYSQL_USER=root
# MYSQL_PASSWORD=your_mysql_password
# MYSQL_DB=docdb
# MYSQL_PORT=3306

# Run aplikasi (otomatis setup backend + frontend)
run.bat
```

Script `run.bat` akan:

- Membuat virtual environment Python (jika belum ada)
- Install dependencies backend
- Install dependencies frontend (jika belum ada)
- Run backend di `http://127.0.0.1:8001`
- Run frontend di `http://localhost:5173`
- Membuat akun admin default otomatis

> **ℹ️ Note**: Pastikan MySQL sudah terinstall dan database `docdb` sudah dibuat. Jika Anda memiliki data SQLite lama, gunakan `python scripts/migrate_sqlite_to_mysql.py` untuk migrasi data.

### Setup Manual

#### Backend

```bash
# Clone repository
git clone https://github.com/Anantarf/4IA19_Kelompok-6_Arsip-Kelurahan---Document-Automation-Classifier.git
cd 4IA19_Kelompok-6_Arsip-Kelurahan---Document-Automation-Classifier

# Buat virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# atau source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env dengan konfigurasi Anda

# Initialize database
python -c "from app.database import init_db; init_db()"

# Run backend
uvicorn app.main:app --reload
```

Backend akan berjalan di `http://127.0.0.1:8001`

### Setup Frontend

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

Frontend akan berjalan di `http://localhost:5173`

## 📋 Default Login

**Admin Account (Created Automatically):**

- **Username**: `admin`
- **Password**: `admin123`
- **Role**: `admin`

**Register:** Silakan buat akun baru melalui halaman register atau gunakan admin untuk membuat user baru.

## 🐳 Docker Deployment

```bash
# Build and run with docker-compose
docker-compose up -d

# Check logs
docker-compose logs -f

# Stop containers
docker-compose down
```

Services akan tersedia di:

- Backend: `http://localhost:8001`
- Frontend: `http://localhost:5173`
- API Docs: `http://localhost:8001/docs`

## 🌐 Production Deployment

### Backend

1. Update `.env` dengan production values:
   ```dotenv
   APP_ENV=production
   APP_DEBUG=false
   LOG_LEVEL=WARNING
   SECRET_KEY=<generate-strong-secret-key>
   CORS_ORIGINS=https://yourdomain.com
   ```
2. Use production ASGI server:
   ```bash
   gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
   ```
3. Setup Nginx reverse proxy
4. Enable HTTPS with SSL certificates

### Frontend

1. Build for production:
   ```bash
   cd frontend
   npm run build
   ```
2. Serve `dist/` folder with Nginx/Apache
3. Update `VITE_API_BASE` to production API URL
4. Configure CSP headers

### Database

- Production database: MySQL 8.0+ (migrated from SQLite)
- Setup regular backups with MySQL tools
- Implement audit logging for compliance
- Monitor connection pooling and performance

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed production setup guide.

## 📁 Struktur Direktori

```
app/
  main.py              # Entry FastAPI
  config.py            # Settings (dotenv)
  database.py          # SQLAlchemy engine & session
  models.py            # SQLAlchemy models
  schemas.py           # Pydantic schemas
  routers/
    upload.py
    search.py
    export.py
  services/
    parser_docx.py
    parser_pdf.py
    ocr.py
    metadata.py
    classifier.py
    foldering.py
  utils/
    audit.py
    hash.py
    slugs.py
scripts/
  migrate_sqlite_to_mysql.py  # Migrasi database ke MySQL ✅ COMPLETED
  recover_documents.py # Recovery dokumen dari metadata.json ✅ VERIFIED
  monitor_consistency.py      # Monitor konsistensi data ✅ ACTIVE
  cleanup_invalid_docs.py     # Cleanup dokumen invalid
  generate_training_data.py   # Generate data training ML
  train_classifier.py  # Training model klasifikasi
  test_ocr.py          # Test OCR functionality
storage/
  uploads/             # Temp upload
  arsip_kelurahan/     # Output akhir (tahun/jenis/...)
```

## Catatan

- Pastikan **Tesseract** terpasang dan dapat dipanggil; untuk Bahasa Indonesia gunakan traineddata `ind`.
- Untuk PDF teks, sistem akan parsing tanpa OCR; OCR hanya digunakan bila konten teks tidak terbaca.
- Internal model field `nomor` telah distandarkan menjadi **`nomor_surat`** pada kode & skema; DB **kolom** tetap `nomor` sehingga tidak perlu migrasi schema. Endpoint upload saat ini mengembalikan kedua kunci `nomor` (legacy) dan `nomor_surat` (kanonik) untuk kompatibilitas.
- Sistem menggunakan **MySQL** untuk persistent storage (sudah dimigrasikan dari SQLite menggunakan `scripts/migrate_sqlite_to_mysql.py`).
- **Data Recovery**: Jika terjadi inkonsistensi data, gunakan recovery dari `metadata.json` files di storage dengan `scripts/recover_documents.py`.
- **Rate Limiting**: API dilengkapi rate limiting untuk mencegah abuse (konfigurasikan di environment variables jika perlu).
- **Security**: CORS dan Trusted Host middleware aktif untuk production security.

---

## OCR setup (Windows — recommended: PyMuPDF fallback)

Jika file PDF yang diunggah adalah hasil scan (gambar), sistem akan mencoba ekstraksi teks via OCR.
Untuk menggunakan OCR pada Windows, ikuti langkah berikut:

1. Install Python dependencies (di dalam virtualenv):

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

(Paket penting: `pytesseract`, `Pillow`, `PyMuPDF` — sudah tercantum di `requirements.txt`.)

2. Install Tesseract engine (Windows):
   - Unduh installer dari: https://github.com/tesseract-ocr/tesseract/releases
   - Secara default Tesseract akan terpasang di: `C:\Program Files\Tesseract-OCR\tesseract.exe`

3. Set Tesseract path di `.env`:

```dotenv
# Jika Tesseract tidak di PATH, isi path lengkap seperti contoh berikut
TESSERACT_CMD="C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
```

4. Restart server:

```powershell
uvicorn app.main:app --reload
```

5. Test OCR cepat:

```powershell
python scripts/test_ocr.py
```

Catatan:

- Jika kamu lebih suka `pdf2image` + `poppler`, kamu bisa menambah `pdf2image` ke environment, namun pada Windows `PyMuPDF` sering lebih mudah di-setup.
- Jika OCR tidak berjalan namun file memiliki metadata di filename (mis. `SM`/`SK` atau ada tahun), parser akan tetap mencoba ekstraksi dari filename/nomor sebagai fallback.

---

## Health check (opsional)

Untuk memeriksa status OCR dari aplikasi (apakah `pytesseract`, `PyMuPDF` tersedia, dan apakah `TESSERACT_CMD` terdeteksi), panggil endpoint:

```bash
curl http://127.0.0.1:8001/healthz/ocr
```

Contoh respons ketika OCR tersedia:

```json
{ "ocr": true, "details": { "pytesseract": true, "pymupdf": true, "tesseract_cmd": "C:\\Program Files\\Tesseract-OCR\\tesseract.exe", "tesseract_cmd_exists": true, "tesseract_version": "4.1.1" } }
```

Jika `ocr` false, cek `README` bagian OCR setup dan pastikan Tesseract terinstal serta `TESSERACT_CMD` di `.env` mengarah ke executable yang benar.

---

## 🔧 Troubleshooting

### Masalah Umum

#### 1. Folder Kosong yang Masih Muncul di UI

**Gejala**: Folder tahun muncul di browser tapi kosong saat diklik.

**Penyebab**: Inkonsistensi antara data di database dan file di storage.

**Solusi**:

```bash
# Cek jumlah file di storage vs database
python -c "
from pathlib import Path
from app.database import SessionLocal
from app.models import Document

# Hitung file di storage
storage_path = Path('storage/arsip_kelurahan')
metadata_files = list(storage_path.rglob('metadata.json'))
print(f'File di storage: {len(metadata_files)}')

# Hitung record di database
db = SessionLocal()
db_count = db.query(Document).count()
print(f'Record di database: {db_count}')
db.close()
"

# Jika ada perbedaan, recover data dari metadata.json
python scripts/recover_documents.py
```

#### 2. Dokumen Tidak Muncul Setelah Upload

**Gejala**: File berhasil diupload tapi tidak muncul di pencarian.

**Penyebab**: Gagal menyimpan record ke database atau error parsing metadata.

**Solusi**:

```bash
# Cek logs aplikasi (jika tersedia)
# tail -f logs/app.log

# Test API connectivity
curl http://localhost:8001/healthz

# Verifikasi database connection
python -c "from app.database import SessionLocal; db = SessionLocal(); print('MySQL connection OK'); db.close()"
```

#### 3. Server Tidak Bisa Start

**Gejala**: Error saat menjalankan `uvicorn app.main:app`

**Penyebab**: Missing dependencies atau konfigurasi environment.

**Solusi**:

```bash
# Reinstall dependencies
pip install -r requirements.txt

# Cek .env file
cat .env

# Test import modules
python -c "from app.main import app; print('Import OK')"
```

#### 4. OCR Tidak Berfungsi

**Gejala**: PDF scan tidak terdeteksi teksnya.

**Penyebab**: Tesseract tidak terinstall atau path salah.

**Solusi**:

```bash
# Test OCR
python scripts/test_ocr.py

# Cek Tesseract installation
tesseract --version

# Update .env jika perlu
echo "TESSERACT_CMD=C:\\Program Files\\Tesseract-OCR\\tesseract.exe" >> .env
```

---

## 🧪 Testing

### Backend Tests

```bash
# Install pytest jika belum ada
pip install pytest

# Run unit tests
pytest tests/

# Run dengan verbose output
pytest tests/ -v

# Test specific module
python -m pytest tests/test_text_extractor.py -v
python -m pytest tests/test_nomor_surat.py -v
```

### Frontend Tests

```bash
cd frontend

# Run unit tests
npm test

# Run with coverage
npm run test:coverage
```

### Integration Tests

```bash
# Test API endpoints
curl http://localhost:8001/healthz
curl http://localhost:8001/

# Test database connection
python -c "from app.database import SessionLocal; db = SessionLocal(); print('MySQL connection OK'); db.close()"

# Test OCR functionality
python scripts/test_ocr.py
```

## 🔧 Maintenance

- **Backup Database**: Use MySQL backup tools (`mysqldump`) regularly
- **Database Migration**: Migration to MySQL completed using `scripts/migrate_sqlite_to_mysql.py`
- **Data Consistency**: Monitor file count vs database records regularly using `scripts/monitor_consistency.py`
- **Clear Temp Files**: Cleanup `storage/uploads/` dan `storage/tmp_ocr/` periodically
- **Update ML Model**: Replace `data/classifier.pkl` with retrained model
- **Monitor Storage**: Check `storage/arsip_kelurahan/` disk usage

### Data Consistency Check

```bash
# Cek konsistensi data secara berkala
python scripts/monitor_consistency.py

# Jika ada inkonsistensi, recover data
python scripts/recover_documents.py

# Atau manual check
python -c "
from pathlib import Path
from app.database import SessionLocal
from app.models import Document

storage_path = Path('storage/arsip_kelurahan')
metadata_files = list(storage_path.rglob('metadata.json'))

db = SessionLocal()
db_count = db.query(Document).count()
db.close()

print(f'Storage files: {len(metadata_files)}')
print(f'Database records: {db_count}')

if len(metadata_files) != db_count:
    print('⚠️  WARNING: Data inconsistency detected!')
    print('Run: python scripts/recover_documents.py')
"
```

See maintenance procedures in the Troubleshooting section above.

---

## 📈 Recent Updates (Januari 2026)

- ✅ **Database Migration**: SQLite → MySQL completed successfully
- ✅ **Security Enhancements**: Rate limiting, CORS, Trusted Host middleware added
- ✅ **Data Integrity**: Consistency monitoring and recovery tools implemented
- ✅ **Testing**: Backend tests (6/6 passed), Frontend tests available
- ✅ **Port Configuration**: Backend moved to port 8001 for better compatibility
- ✅ **Dependencies**: Updated with PyMySQL, slowapi for production readiness

**Current Status**: Application is production-ready with persistent MySQL storage, comprehensive security, and monitoring capabilities.

## 📚 Documentation

- **API Documentation**: `http://localhost:8001/docs` (Swagger UI)
- **API Redoc**: `http://localhost:8001/redoc`

## 👥 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## 📄 License

This project is for educational purposes (P3L - Informatika).

Made with ❤️ for Kelurahan Pela Mampang
