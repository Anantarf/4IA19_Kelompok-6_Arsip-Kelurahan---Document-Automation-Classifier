import React, { useCallback, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useUploadDocument } from '../hooks/useUploadDocument';
import { getJenisLabel } from '../utils/jenis';
import { useDropzone } from 'react-dropzone';
import { Upload, X, CheckCircle, AlertCircle, FileText, Loader2, Save } from 'lucide-react';
import api from '../api/axios';
import { useNotification } from '../contexts/NotificationContext';
import { MAX_FILE_SIZE } from '../config/constants';
import { useObjectUrl } from '../hooks/useObjectUrl';

type ParsedMetadata = {
  nomor?: string | null;
  perihal?: string | null;
  tanggal_surat?: string | null;
  jenis?: 'masuk' | 'keluar' | 'lainnya' | null;
};

type DuplicateInfo = {
  duplicate_of: number;
  nomor_surat: string;
  tanggal_surat?: string;
  jenis: string;
  uploaded_at?: string;
};

export default function UploadPage() {
  const navigate = useNavigate();
  const { mutate, isLoading: isUploading, isSuccess, reset: resetMutation } = useUploadDocument();
  const [file, setFile] = useState<File | null>(null);
  const previewUrl = useObjectUrl(file);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analyzeError, setAnalyzeError] = useState('');
  const [parsedMeta, setParsedMeta] = useState<ParsedMetadata | null>(null);
  const { addNotification } = useNotification();
  const [uploadResult, setUploadResult] = useState<any>(null);
  const [duplicateInfo, setDuplicateInfo] = useState<DuplicateInfo | null>(null);
  const [showDuplicateDialog, setShowDuplicateDialog] = useState(false);
  const userConfirmedDuplicate = React.useRef(false);

  // Reset upload result jika file baru dipilih
  React.useEffect(() => {
    setUploadResult(null);
  }, [file]);

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      if (!acceptedFiles?.[0]) return;
      const selectedFile = acceptedFiles[0];

      // Validate size
      if (selectedFile.size > MAX_FILE_SIZE) {
        setAnalyzeError(
          `File terlalu besar (${(selectedFile.size / (1024 * 1024)).toFixed(
            1,
          )} MB). Maksimal ${(MAX_FILE_SIZE / (1024 * 1024)).toFixed(0)} MB.`,
        );
        setFile(null);
        return;
      }

      setFile(selectedFile);
      setParsedMeta(null);
      setAnalyzeError('');
      setDuplicateInfo(null);
      setShowDuplicateDialog(false);
      userConfirmedDuplicate.current = false;
      resetMutation();

      // Preview for PDFs only – useObjectUrl hook handles it

      // Analyze metadata
      setIsAnalyzing(true);
      const formData = new FormData();
      formData.append('file', selectedFile);
      try {
        const res = await api.post('/upload/analyze', formData);
        const { parsed, duplicate } = res.data;
        if (parsed) {
          setParsedMeta(parsed);
        }
        
        // Check for duplicate
        if (duplicate) {
          setDuplicateInfo(duplicate);
          setShowDuplicateDialog(true);
        }
      } catch (err) {
        console.error('Analysis failed', err);
        setAnalyzeError('Gagal menganalisis otomatis. Periksa kualitas dokumen lalu coba lagi.');
        // Reset file to prevent uploading unanalyzed/invalid file
        setFile(null);
        setParsedMeta(null);
        resetMutation();
      } finally {
        setIsAnalyzing(false);
      }
    },
    [resetMutation],
  );

  const { getRootProps, getInputProps } = useDropzone({
    onDrop,
    maxFiles: 1,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    },
  });

  const handleUpload = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!file) return;
    
    // If duplicate detected and user hasn't confirmed yet, don't proceed
    if (duplicateInfo && !userConfirmedDuplicate.current) {
      // Dialog is already visible (set by onDrop), just return
      return;
    }
    
    const formData = new FormData();
    formData.append('file', file);
    mutate(formData, {
      onSuccess: (data: any) => {
        setUploadResult(data);
        if (data.duplicate_of) {
          addNotification(
            `⚠️ Info: File ini sudah ada di sistem (Duplikat dari dokumen #${data.duplicate_of}).`,
          );
        } else {
          addNotification('Dokumen berhasil diunggah');
        }
      },
    });
  };

  const handleReset = () => {
    setFile(null);
    setAnalyzeError('');
    setParsedMeta(null);
    setDuplicateInfo(null);
    setShowDuplicateDialog(false);
    userConfirmedDuplicate.current = false;
    resetMutation();
  };

  const metadataItems = useMemo(() => {
    const items = [
      { label: 'Nama File', value: file?.name || '-' },
      { label: 'Nomor Dokumen', value: parsedMeta?.nomor },
    ];
    if (parsedMeta?.jenis === 'masuk') {
      items.push({ label: 'Perihal', value: parsedMeta?.perihal });
    }
    items.push({
      label: 'Jenis Dokumen',
      value: getJenisLabel(parsedMeta?.jenis),
    });
    items.push({ label: 'Tanggal Dokumen', value: parsedMeta?.tanggal_surat });
    return items;
  }, [file?.name, parsedMeta]);

  if (isSuccess) {
    return (
      <div className="max-w-2xl mx-auto animate-fade-in py-12">
        <div className="bg-green-50 border border-green-100 rounded-2xl p-8 text-center shadow-sm">
          <div className="w-16 h-16 bg-green-100 text-green-600 rounded-full flex items-center justify-center mx-auto mb-4">
            <CheckCircle size={32} />
          </div>
          <h3 className="text-xl font-bold text-green-800 mb-2">Berhasil diunggah!</h3>
          <p className="text-green-700 mb-6">Dokumen sudah tersimpan.</p>
          <div className="flex justify-center gap-3">
            <button onClick={handleReset} className="btn-primary">
              Unggah Lagi
            </button>
            <button onClick={() => navigate('/search')} className="btn-secondary">
              Lihat Dokumen
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto animate-fade-in h-[calc(100vh-8rem)] flex flex-col">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 tracking-tight">Unggah Dokumen</h1>
          <p className="text-slate-600 text-sm mt-2 font-normal leading-relaxed">
            Periksa dokumen sebelum disimpan.
          </p>
        </div>
      </div>
      {!file ? (
        <div
          {...getRootProps()}
          className="flex-none bg-white rounded-2xl border-2 border-dashed border-slate-300 hover:border-primary-500 hover:bg-slate-50/50 transition-all cursor-pointer p-8 sm:p-12 flex flex-col items-center justify-center min-h-[280px] sm:min-h-[380px]"
        >
          <input {...getInputProps()} />
          <div className="text-center max-w-md">
            <div className="w-16 h-16 bg-primary-50 text-user-primary rounded-2xl flex items-center justify-center mx-auto mb-4 text-primary-600">
              <Upload size={32} />
            </div>
            <h3 className="text-lg sm:text-xl font-semibold text-slate-900 mb-1">Unggah Dokumen</h3>
            <p className="text-slate-500 mb-2 text-sm sm:text-base">
              Klik atau tarik file PDF/DOCX ke sini.
            </p>
            <p className="text-xs text-slate-400">Sistem akan otomatis membaca info dokumen.</p>
          </div>
        </div>
      ) : (
        <div className="flex-1 grid grid-cols-1 sm:grid-cols-2 gap-4 lg:gap-6 min-h-0">
          {/* Left: Preview */}
          <div className="bg-slate-800 rounded-xl overflow-hidden shadow-md flex flex-col relative order-2 sm:order-1">
            <div className="bg-slate-900 px-4 py-3 flex items-center justify-between shadow-sm z-10">
              <div className="flex items-center gap-3 text-white overflow-hidden">
                <FileText size={18} className="text-slate-400 shrink-0" />
                <span className="text-sm font-medium truncate">{file.name}</span>
              </div>
              <button
                onClick={handleReset}
                className="text-slate-400 hover:text-white p-1 rounded-md hover:bg-slate-800 transition-colors"
              >
                <X size={18} />
              </button>
            </div>
            <div className="flex-1 bg-slate-200 relative">
              {previewUrl ? (
                <iframe
                  src={previewUrl}
                  className="w-full h-full border-none"
                  title="Pratinjau Dokumen"
                />
              ) : (
                <div className="absolute inset-0 flex flex-col items-center justify-center text-slate-500">
                  <FileText size={48} className="mb-2 opacity-50" />
                  <p>Pratinjau belum tersedia untuk format ini.</p>
                  <p className="text-xs mt-1">(Pratinjau langsung hanya untuk PDF)</p>
                </div>
              )}
              {isAnalyzing && (
                <div className="absolute inset-0 bg-white/80 backdrop-blur-sm z-20 flex flex-col items-center justify-center text-primary-600">
                  <Loader2 size={40} className="animate-spin mb-4" />
                  <p className="font-semibold animate-pulse">Sedang memproses dokumen...</p>
                  <p className="text-xs text-slate-500 mt-1">Mencari nomor dan tanggal</p>
                </div>
              )}
            </div>
          </div>
          {/* Right: Form */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm flex flex-col h-full overflow-hidden order-1 sm:order-2">
            <div className="p-6 border-b border-slate-100">
              <h3 className="font-semibold text-base sm:text-lg text-slate-900 flex items-center gap-2">
                <span className="w-1.5 h-6 bg-primary-600 rounded-full inline-block" /> Periksa Data
              </h3>
              <p className="text-slate-500 text-sm mt-1">
                Data diisi otomatis dari hasil pemindaian.
              </p>
            </div>
            <div className="flex-1 overflow-y-auto p-6 space-y-4">
              {analyzeError && (
                <div className="p-3 bg-amber-50 text-amber-700 text-xs rounded-lg flex gap-2">
                  <AlertCircle size={14} className="mt-0.5 shrink-0" />
                  {analyzeError}
                </div>
              )}
              {duplicateInfo && (
                <div className="p-3 bg-blue-50 border border-blue-200 text-blue-700 text-xs rounded-lg flex gap-2">
                  <AlertCircle size={14} className="mt-0.5 shrink-0" />
                  <div>
                    <p className="font-semibold">File duplikat terdeteksi</p>
                    <p className="mt-1">File ini sudah ada di sistem (Dokumen #{duplicateInfo.duplicate_of}). Klik "Simpan Dokumen" untuk konfirmasi upload.</p>
                  </div>
                </div>
              )}
              <form id="upload-form" onSubmit={handleUpload} className="space-y-3">
                <div className="space-y-3">
                  {metadataItems.map(({ label, value }) => (
                    <div key={label} className="border border-slate-100 rounded-lg p-3 bg-slate-50">
                      <p className="text-xs uppercase text-slate-500 font-semibold">{label}</p>
                      <p className="text-sm text-slate-900 mt-1 break-words">{value || '-'}</p>
                    </div>
                  ))}
                </div>
              </form>
            </div>
            <div className="p-4 bg-slate-50 border-t border-slate-200 flex justify-end gap-3 shrink-0">
              <button onClick={handleReset} className="btn-secondary py-2.5 text-sm">
                Batal
              </button>
              <button
                type="submit"
                form="upload-form"
                disabled={isUploading}
                className="btn-primary py-2.5 flex items-center gap-2 text-sm"
              >
                {isUploading ? (
                  <>
                    <Loader2 size={16} className="animate-spin" />
                    Menyimpan...
                  </>
                ) : (
                  <>
                    <Save size={16} />
                    {isAnalyzing ? 'Simpan (memeriksa...)' : 'Simpan Dokumen'}
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
      
      {/* Duplicate Confirmation Dialog */}
      {showDuplicateDialog && duplicateInfo && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-fade-in">
          <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-6 animate-scale-in">
            <div className="flex items-start gap-4 mb-4">
              <div className="w-12 h-12 bg-amber-100 text-amber-600 rounded-full flex items-center justify-center shrink-0">
                <AlertCircle size={24} />
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-bold text-slate-900 mb-1">File Duplikat Terdeteksi</h3>
                <p className="text-sm text-slate-600">
                  File ini sudah pernah diunggah sebelumnya ke sistem.
                </p>
              </div>
            </div>
            
            <div className="bg-slate-50 rounded-lg p-4 mb-6 space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-slate-600">Dokumen ID:</span>
                <span className="font-semibold text-slate-900">#{duplicateInfo.duplicate_of}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-slate-600">Nomor Surat:</span>
                <span className="font-semibold text-slate-900">{duplicateInfo.nomor_surat}</span>
              </div>
              {duplicateInfo.tanggal_surat && (
                <div className="flex justify-between text-sm">
                  <span className="text-slate-600">Tanggal:</span>
                  <span className="font-semibold text-slate-900">{duplicateInfo.tanggal_surat}</span>
                </div>
              )}
              <div className="flex justify-between text-sm">
                <span className="text-slate-600">Jenis:</span>
                <span className="font-semibold text-slate-900 capitalize">{duplicateInfo.jenis}</span>
              </div>
              {duplicateInfo.uploaded_at && (
                <div className="flex justify-between text-sm">
                  <span className="text-slate-600">Diunggah:</span>
                  <span className="font-semibold text-slate-900">
                    {new Date(duplicateInfo.uploaded_at).toLocaleDateString('id-ID', {
                      day: 'numeric',
                      month: 'long',
                      year: 'numeric',
                    })}
                  </span>
                </div>
              )}
            </div>
            
            <p className="text-sm text-slate-600 mb-6">
              Apakah Anda yakin ingin mengunggah file ini lagi? File duplikat akan tetap disimpan dengan referensi ke dokumen asli.
            </p>
            
            <div className="flex gap-3">
              <button
                onClick={handleReset}
                className="flex-1 btn-secondary py-2.5 text-sm"
              >
                Batal
              </button>
              <button
                onClick={() => {
                  // Set confirmation flag first
                  userConfirmedDuplicate.current = true;
                  setShowDuplicateDialog(false);
                  // User confirmed, proceed with upload
                  const form = document.getElementById('upload-form') as HTMLFormElement;
                  if (form) {
                    form.requestSubmit();
                  }
                }}
                className="flex-1 btn-primary py-2.5 text-sm"
              >
                Ya, Unggah
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
