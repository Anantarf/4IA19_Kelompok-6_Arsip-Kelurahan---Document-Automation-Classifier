"""
Training Script untuk Document Classifier
Menggunakan dummy sample dari kelurahan untuk training model ML

Requirements:
- scikit-learn
- joblib

Install: pip install scikit-learn joblib
"""

import sys
from pathlib import Path
import json
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.models import Document

def collect_training_data():
    """
    Collect training data from existing documents in database.
    Returns: (texts, labels)
    """
    db = SessionLocal()
    try:
        # Get all documents with valid jenis
        docs = db.query(Document).filter(
            Document.jenis.in_(['masuk', 'keluar'])
        ).all()
        
        texts = []
        labels = []
        
        for doc in docs:
            # Read text content if available
            if doc.metadata_path:
                metadata_path = Path(doc.metadata_path)
                if metadata_path.exists():
                    try:
                        with open(metadata_path, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                            
                        # Combine relevant text fields for training
                        text_parts = []
                        if doc.nomor_surat:
                            text_parts.append(doc.nomor_surat)
                        if doc.perihal:
                            text_parts.append(doc.perihal)
                        if doc.pengirim:
                            text_parts.append(f"dari {doc.pengirim}")
                        if doc.penerima:
                            text_parts.append(f"kepada {doc.penerima}")
                        
                        # Read full text if available
                        text_path = metadata.get('text_path')
                        if text_path:
                            text_file = Path(text_path)
                            if text_file.exists():
                                with open(text_file, 'r', encoding='utf-8') as f:
                                    text_parts.append(f.read()[:5000])  # Limit to 5000 chars
                        
                        if text_parts:
                            texts.append(' '.join(text_parts))
                            labels.append(doc.jenis)
                            
                    except Exception as e:
                        print(f"⚠️  Error reading doc #{doc.id}: {e}")
        
        return texts, labels
        
    finally:
        db.close()


def train_classifier(texts, labels, model_path='data/classifier_model.pkl'):
    """
    Train ML classifier using collected data.
    """
    if len(texts) < 10:
        print("[ERROR] Tidak cukup data training (minimal 10 dokumen)")
        print("   Silakan upload lebih banyak dokumen dummy dari kelurahan")
        return None
    
    print(f"[*] Training dengan {len(texts)} dokumen...")
    print(f"   Surat Masuk: {labels.count('masuk')}")
    print(f"   Surat Keluar: {labels.count('keluar')}")
    print()
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        texts, labels, test_size=0.2, random_state=42, stratify=labels
    )
    
    # Create pipeline
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(
            max_features=1000,
            ngram_range=(1, 2),
            min_df=2,
            stop_words=None  # Keep Indonesian stopwords for now
        )),
        ('classifier', MultinomialNB(alpha=0.1))
    ])
    
    # Train
    print("🔧 Training model...")
    pipeline.fit(X_train, y_train)
    
    # Evaluate
    y_pred = pipeline.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    
    print(f"\n[OK] Training selesai!")
    print(f"   Accuracy: {accuracy:.2%}")
    print("\n📈 Classification Report:")
    print(classification_report(y_test, y_pred, target_names=['masuk', 'keluar']))
    
    # Save model
    model_dir = Path(model_path).parent
    model_dir.mkdir(parents=True, exist_ok=True)
    
    joblib.dump(pipeline, model_path)
    print(f"\n💾 Model disimpan ke: {model_path}")
    
    return pipeline


def test_predictions(pipeline, sample_texts):
    """
    Test model predictions on sample texts.
    """
    print("\n🧪 Testing predictions:")
    print("-" * 60)
    
    for text in sample_texts:
        prediction = pipeline.predict([text])[0]
        proba = pipeline.predict_proba([text])[0]
        confidence = max(proba)
        
        preview = text[:100] + "..." if len(text) > 100 else text
        print(f"\nText: {preview}")
        print(f"Prediction: {prediction} (confidence: {confidence:.2%})")


def main():
    print("=" * 60)
    print("[*] Document Classifier Training")
    print("=" * 60)
    print()
    
    # Step 1: Collect data
    print("📁 Mengumpulkan training data dari database...")
    texts, labels = collect_training_data()
    
    if len(texts) == 0:
        print("[ERROR] Tidak ada data training!")
        print("   Cara menggunakan:")
        print("   1. Upload dokumen dummy dari kelurahan (min 10 dokumen)")
        print("   2. Pastikan dokumen sudah dilabeli (jenis: masuk/keluar)")
        print("   3. Jalankan script ini lagi")
        return
    
    print(f"[OK] Berhasil mengumpulkan {len(texts)} dokumen")
    print()
    
    # Step 2: Train model
    pipeline = train_classifier(texts, labels)
    
    if pipeline is None:
        return
    
    # Step 3: Test predictions
    sample_texts = [
        "Kepada Yth. Bapak Lurah Pela Mampang, Perihal: Permohonan Izin Keramaian",
        "Dari: Dinas Pendidikan Jakarta Selatan, Perihal: Undangan Rapat Koordinasi",
        "Nomor: 001/SK/I/2025, Surat Keputusan tentang Pembentukan Tim Kerja",
        "Pengirim: Ketua RT 05, Perihal: Laporan Kegiatan Posyandu"
    ]
    
    test_predictions(pipeline, sample_texts)
    
    print("\n" + "=" * 60)
    print("✨ Training selesai!")
    print("=" * 60)
    print("\nUntuk menggunakan model:")
    print("1. Edit app/services/classifier.py")
    print("2. Load model dengan: joblib.load('data/classifier_model.pkl')")
    print("3. Gunakan pipeline.predict(text) untuk klasifikasi")


if __name__ == "__main__":
    main()
