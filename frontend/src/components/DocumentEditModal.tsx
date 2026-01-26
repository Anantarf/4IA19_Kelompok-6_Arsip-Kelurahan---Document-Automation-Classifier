import React from 'react';
import { X, Save, AlertTriangle, CheckCircle, XCircle, Loader2 } from 'lucide-react';
import { updateDocument, type DocumentUpdate } from '../api/documents';
import type { Document } from '../types';
import { getJenisLabel } from '../utils/jenis';
import { useNotification } from '../contexts/NotificationContext';

type DocumentEditModalProps = {
  doc: Document;
  onClose: () => void;
  onUpdated: (updatedDoc: Document) => void;
};

type FormState = 'idle' | 'submitting' | 'success' | 'error';

export default function DocumentEditModal({ doc, onClose, onUpdated }: DocumentEditModalProps) {
  const { addNotification } = useNotification();
  const [formData, setFormData] = React.useState<DocumentUpdate>({
    nomor_surat: doc.nomor_surat || '',
    perihal: doc.perihal || '',
    tanggal_surat: doc.tanggal_surat || '',
    jenis: doc.jenis,
    pengirim: doc.pengirim || '',
    penerima: doc.penerima || '',
  });
  const [confirmSensitive, setConfirmSensitive] = React.useState(false);
  const [formState, setFormState] = React.useState<FormState>('idle');
  const [error, setError] = React.useState<string | null>(null);
  const [successMessage, setSuccessMessage] = React.useState<string | null>(null);

  const hasSensitiveChanges = React.useMemo(() => {
    return (
      (formData.tanggal_surat && formData.tanggal_surat !== doc.tanggal_surat) ||
      (formData.jenis && formData.jenis !== doc.jenis)
    );
  }, [formData.tanggal_surat, formData.jenis, doc.tanggal_surat, doc.jenis]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccessMessage(null);

    if (hasSensitiveChanges && !confirmSensitive) {
      setError(
        'Mengubah tanggal atau jenis surat memerlukan konfirmasi. Centang kotak konfirmasi di bawah.',
      );
      return;
    }

    setFormState('submitting');
    try {
      const updates = {
        ...formData,
        confirm_sensitive: hasSensitiveChanges ? confirmSensitive : undefined,
      };
      const updatedDoc = await updateDocument(doc.id, updates);
      setFormState('success');
      setSuccessMessage('Metadata dokumen berhasil diperbarui!');

      // Add notification
      addNotification(
        `Metadata dokumen "${doc.original_filename || doc.perihal || 'Tanpa nama'}" berhasil diperbarui`,
      );

      // Auto-close after success
      setTimeout(() => {
        onUpdated(updatedDoc);
        onClose();
      }, 1500);
    } catch (err: any) {
      setFormState('error');
      setError(err.response?.data?.detail || 'Gagal memperbarui dokumen');
    }
  };

  const handleInputChange = (field: keyof DocumentUpdate, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-2 sm:p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div className="p-4 sm:p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg sm:text-xl font-bold text-slate-900">Edit Metadata Dokumen</h2>
            <button
              onClick={onClose}
              className="p-2 text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-lg transition-all"
            >
              <X size={20} />
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Nomor Surat */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Nomor Dokumen</label>
              <input
                type="text"
                value={formData.nomor_surat || ''}
                onChange={(e) => handleInputChange('nomor_surat', e.target.value)}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                placeholder="Masukkan nomor dokumen"
              />
            </div>

            {/* Perihal */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Perihal</label>
              <input
                type="text"
                value={formData.perihal || ''}
                onChange={(e) => handleInputChange('perihal', e.target.value)}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                placeholder="Masukkan perihal dokumen"
              />
            </div>

            {/* Tanggal Surat */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                Tanggal Dokumen
              </label>
              <input
                type="date"
                value={formData.tanggal_surat || ''}
                onChange={(e) => handleInputChange('tanggal_surat', e.target.value)}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              />
            </div>

            {/* Jenis Dokumen */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Jenis Dokumen</label>
              <select
                value={formData.jenis || ''}
                onChange={(e) => handleInputChange('jenis', e.target.value as Document['jenis'])}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              >
                <option value="masuk">{getJenisLabel('masuk')}</option>
                <option value="keluar">{getJenisLabel('keluar')}</option>
                <option value="lainnya">{getJenisLabel('lainnya')}</option>
              </select>
            </div>

            {/* Pengirim */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Pengirim</label>
              <input
                type="text"
                value={formData.pengirim || ''}
                onChange={(e) => handleInputChange('pengirim', e.target.value)}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                placeholder="Masukkan nama pengirim"
              />
            </div>

            {/* Penerima */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Penerima</label>
              <input
                type="text"
                value={formData.penerima || ''}
                onChange={(e) => handleInputChange('penerima', e.target.value)}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                placeholder="Masukkan nama penerima"
              />
            </div>

            {/* Sensitive Changes Confirmation */}
            {hasSensitiveChanges && (
              <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
                <div className="flex items-start gap-3">
                  <AlertTriangle className="text-amber-600 mt-0.5 flex-shrink-0" size={20} />
                  <div className="flex-1">
                    <h4 className="text-sm font-medium text-amber-800 mb-2">
                      Konfirmasi Perubahan Sensitif
                    </h4>
                    <p className="text-sm text-amber-700 mb-3">
                      Anda mengubah tanggal atau jenis dokumen. Perubahan ini dapat mempengaruhi
                      pengarsipan dan pencarian. Pastikan data yang dimasukkan sudah benar.
                    </p>
                    <label className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={confirmSensitive}
                        onChange={(e) => setConfirmSensitive(e.target.checked)}
                        className="rounded border-slate-300 text-primary-600 focus:ring-primary-500"
                      />
                      <span className="text-sm text-amber-800">
                        Saya yakin dengan perubahan ini
                      </span>
                    </label>
                  </div>
                </div>
              </div>
            )}

            {/* Status Messages */}
            {error && formState === 'error' && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4 animate-fade-in">
                <div className="flex items-start gap-3">
                  <XCircle className="text-red-600 mt-0.5 flex-shrink-0" size={20} />
                  <div className="flex-1">
                    <h4 className="text-sm font-medium text-red-800 mb-1">Error</h4>
                    <p className="text-sm text-red-700">{error}</p>
                  </div>
                </div>
              </div>
            )}

            {successMessage && formState === 'success' && (
              <div className="bg-green-50 border border-green-200 rounded-lg p-4 animate-fade-in">
                <div className="flex items-start gap-3">
                  <CheckCircle className="text-green-600 mt-0.5 flex-shrink-0" size={20} />
                  <div className="flex-1">
                    <h4 className="text-sm font-medium text-green-800 mb-1">Berhasil</h4>
                    <p className="text-sm text-green-700">{successMessage}</p>
                  </div>
                </div>
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-200">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 text-slate-700 hover:text-slate-900 hover:bg-slate-100 rounded-lg transition-all disabled:opacity-50"
                disabled={formState === 'submitting'}
              >
                Batal
              </button>
              <button
                type="submit"
                disabled={formState === 'submitting' || (hasSensitiveChanges && !confirmSensitive)}
                className={`px-4 py-2 rounded-lg transition-all flex items-center gap-2 ${
                  formState === 'submitting'
                    ? 'bg-slate-400 text-slate-100 cursor-not-allowed'
                    : formState === 'success'
                      ? 'bg-green-600 text-white hover:bg-green-700'
                      : hasSensitiveChanges && !confirmSensitive
                        ? 'bg-slate-300 text-slate-500 cursor-not-allowed'
                        : 'bg-primary-600 text-white hover:bg-primary-700'
                }`}
              >
                {formState === 'submitting' ? (
                  <>
                    <Loader2 size={16} className="animate-spin" />
                    Menyimpan...
                  </>
                ) : formState === 'success' ? (
                  <>
                    <CheckCircle size={16} />
                    Tersimpan
                  </>
                ) : (
                  <>
                    <Save size={16} />
                    Simpan Perubahan
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
