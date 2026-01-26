import React from 'react';
import { Download, Edit2, FileText, Trash2, X, Edit3, Loader2 } from 'lucide-react';
import api from '../api/axios';
import type { Document } from '../types';
import PDFPreview from './PDFPreview';
import { getJenisLabel } from '../utils/jenis';
import DocumentEditModal from './DocumentEditModal';

type DocumentModalProps = {
  doc: Document;
  onClose: () => void;
  onRename?: () => void;
  onDelete?: () => void;
  onConfirmDelete?: () => void;
  confirmDelete?: boolean;
  onConfirmDeleteChange?: (value: boolean) => void;
  isDeleting?: boolean;
  canEdit?: boolean;
  canDelete?: boolean;
  onDocumentUpdated?: (updatedDoc: Document) => void;
};

export default function DocumentModal({
  doc,
  onClose,
  onRename,
  onDelete,
  onConfirmDelete,
  confirmDelete,
  onConfirmDeleteChange,
  isDeleting,
  canEdit,
  canDelete,
  onDocumentUpdated,
}: DocumentModalProps) {
  const [showEditModal, setShowEditModal] = React.useState(false);
  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-2 sm:p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-7xl max-h-[99vh] h-[90vh] overflow-hidden flex flex-col animate-scale-in">
        {/* Modal Header */}
        <div className="p-4 sm:p-6 border-b border-slate-200 flex items-center justify-between bg-slate-50 shrink-0">
          <h2
            className="text-lg sm:text-xl font-bold text-slate-900 truncate"
            title={doc.original_filename || doc.perihal || 'Dokumen'}
          >
            {doc.original_filename || doc.perihal || 'Dokumen'}
          </h2>
          <div className="flex items-center gap-1 sm:gap-2">
            {canEdit && (
              <button
                onClick={() => setShowEditModal(true)}
                className="p-2 text-slate-600 hover:text-blue-600 hover:bg-slate-100 rounded-lg transition-all"
                title="Edit Metadata"
                disabled={showEditModal}
              >
                <Edit3 size={18} />
              </button>
            )}
            {canEdit && onRename && (
              <button
                onClick={onRename}
                className="p-2 text-slate-600 hover:text-primary-600 hover:bg-slate-100 rounded-lg transition-all"
                title="Ubah Nama/Perihal"
              >
                <Edit2 size={18} />
              </button>
            )}
            <button
              onClick={() => {
                const token = localStorage.getItem('token');
                const url = `${api.defaults.baseURL}/documents/${doc.id}/file`;
                const link = document.createElement('a');
                link.href = url;
                link.setAttribute('download', doc.original_filename || doc.perihal || 'dokumen');
                if (token) {
                  fetch(url, { headers: { Authorization: `Bearer ${token}` } })
                    .then((res) => res.blob())
                    .then((blob) => {
                      const blobUrl = window.URL.createObjectURL(blob);
                      link.href = blobUrl;
                      link.click();
                      window.URL.revokeObjectURL(blobUrl);
                    });
                } else {
                  link.click();
                }
              }}
              className="p-2 text-slate-600 hover:text-green-600 hover:bg-slate-100 rounded-lg transition-all"
              title="Unduh"
            >
              <Download size={18} />
            </button>
            {canDelete && onDelete && (
              <button
                onClick={onDelete}
                disabled={Boolean(isDeleting)}
                className={`p-2 rounded-lg transition-all ${
                  isDeleting
                    ? 'text-slate-400 cursor-not-allowed'
                    : 'text-slate-600 hover:text-red-600 hover:bg-slate-100'
                }`}
                title="Hapus Dokumen"
              >
                <Trash2 size={18} />
              </button>
            )}
            <button
              onClick={onClose}
              className="p-2 text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-lg transition-all ml-1 sm:ml-2"
              title="Tutup"
            >
              <X size={18} />
            </button>
          </div>
        </div>

        {confirmDelete && canDelete && onConfirmDeleteChange && onConfirmDelete && (
          <div className="px-4 sm:px-6 pb-2">
            <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-red-200 bg-red-50 px-3 py-2">
              <span className="text-xs sm:text-sm text-red-700">Yakin mau hapus dokumen ini?</span>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => onConfirmDeleteChange(false)}
                  disabled={Boolean(isDeleting)}
                  className={`px-3 py-1 text-xs sm:text-sm rounded-md border border-red-200 ${
                    isDeleting
                      ? 'text-red-300 bg-red-50 cursor-not-allowed'
                      : 'text-red-700 hover:bg-red-100'
                  }`}
                >
                  Batal
                </button>
                <button
                  onClick={onConfirmDelete}
                  disabled={Boolean(isDeleting)}
                  className={`px-3 py-1 text-xs sm:text-sm rounded-md text-white ${
                    isDeleting ? 'bg-red-400 cursor-not-allowed' : 'bg-red-600 hover:bg-red-700'
                  }`}
                >
                  {isDeleting ? 'Menghapus...' : 'Hapus'}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Modal Content */}
        <div className="flex-1 overflow-y-auto flex flex-col lg:flex-row gap-4 lg:gap-0">
          {/* Preview */}
          <div className="flex-1 bg-slate-100 p-4 sm:p-6 flex items-center justify-center min-h-[600px] lg:min-h-[600px] h-full">
            {doc.mime_type === 'application/pdf' ? (
              <PDFPreview docId={doc.id} />
            ) : (
              <div className="flex flex-col items-center justify-center text-slate-500">
                <FileText size={80} className="opacity-20 mb-4" />
                <p className="font-semibold text-lg">Pratinjau belum tersedia untuk DOCX.</p>
                <p className="text-sm mt-2">Silakan unduh untuk melihat dokumen.</p>
              </div>
            )}
          </div>

          {/* Metadata Sidebar */}
          <div className="w-full lg:w-1/3 bg-slate-50 border-t lg:border-t-0 lg:border-l border-slate-200 p-4 sm:p-6">
            <h3 className="font-semibold text-slate-900 mb-4 text-base sm:text-lg">Info Dokumen</h3>
            <div className="space-y-3 sm:space-y-4">
              {[
                {
                  label: 'Nama File',
                  value: doc.original_filename || doc.stored_path?.split('/')?.pop(),
                },
                // Only show nomor & perihal if NOT "lainnya"
                ...(doc.jenis === 'masuk'
                  ? [
                      { label: 'Nomor Dokumen', value: doc.nomor_surat },
                      { label: 'Perihal', value: doc.perihal },
                    ]
                  : doc.jenis !== 'lainnya'
                    ? [{ label: 'Nomor Dokumen', value: doc.nomor_surat }]
                    : []),
                { label: 'Jenis Dokumen', value: getJenisLabel(doc.jenis) },
                { label: 'Tanggal Dokumen', value: doc.tanggal_surat },
                { label: 'Pengirim', value: doc.pengirim },
                { label: 'Penerima', value: doc.penerima },
              ].map(({ label, value }) =>
                value ? (
                  <div key={label} className="border-b border-slate-200 pb-3 last:border-b-0">
                    <p className="text-xs font-semibold text-slate-600 uppercase mb-1">{label}</p>
                    <p className="text-sm text-slate-900 break-words">{String(value)}</p>
                  </div>
                ) : null,
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Loading overlay when edit modal is open */}
      {showEditModal && (
        <div className="absolute inset-0 bg-black/10 backdrop-blur-sm z-10 flex items-center justify-center animate-fade-in">
          <div className="bg-white/90 rounded-lg px-4 py-2 shadow-lg flex items-center gap-2">
            <Loader2 size={16} className="animate-spin text-primary-600" />
            <span className="text-sm text-slate-700">Memuat editor...</span>
          </div>
        </div>
      )}

      {showEditModal && (
        <DocumentEditModal
          doc={doc}
          onClose={() => setShowEditModal(false)}
          onUpdated={(updatedDoc) => {
            if (onDocumentUpdated) {
              onDocumentUpdated(updatedDoc);
            }
            setShowEditModal(false);
          }}
        />
      )}
    </div>
  );
}
