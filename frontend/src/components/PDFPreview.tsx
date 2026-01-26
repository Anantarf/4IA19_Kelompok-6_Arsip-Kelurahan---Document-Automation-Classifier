import React, { useEffect, useState } from 'react';
import api from '../api/axios';
import { Loader2, AlertCircle } from 'lucide-react';

interface PDFPreviewProps {
  docId: number;
}

export default function PDFPreview({ docId }: PDFPreviewProps) {
  const [blobUrl, setBlobUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      setError('Tidak terautentikasi. Silakan login kembali.');
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);

    fetch(`${api.defaults.baseURL}/documents/${docId}/file`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res) => {
        if (!res.ok) {
          throw new Error(`HTTP ${res.status}: ${res.statusText}`);
        }
        return res.blob();
      })
      .then((blob) => {
        const url = window.URL.createObjectURL(blob);
        setBlobUrl(url);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Error loading PDF:', err);
        setError(err.message || 'Gagal memuat pratinjau dokumen');
        setLoading(false);
      });

    return () => {
      if (blobUrl) {
        window.URL.revokeObjectURL(blobUrl);
      }
    };
  }, [docId]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-slate-500">
        <Loader2 size={48} className="animate-spin mb-4 opacity-50" />
        <p>Memuat pratinjau...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-red-500">
        <AlertCircle size={48} className="mb-4 opacity-50" />
        <p className="font-semibold">Gagal memuat dokumen</p>
        <p className="text-sm text-slate-600 mt-2">{error}</p>
      </div>
    );
  }

  if (!blobUrl) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-slate-500">
        <p>Tidak ada data untuk ditampilkan</p>
      </div>
    );
  }

  return (
    <iframe
      src={`${blobUrl}#toolbar=0`}
      className="w-full h-[75vh] min-h-[500px] rounded-lg shadow-sm bg-white"
      title="Pratinjau Dokumen PDF"
      style={{ maxHeight: '80vh' }}
    />
  );
}
