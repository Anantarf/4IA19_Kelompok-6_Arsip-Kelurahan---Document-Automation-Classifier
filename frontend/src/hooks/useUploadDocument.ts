import { useMutation, useQueryClient } from '@tanstack/react-query';
import { uploadDocument } from '../api/documents';
import { useNotification } from '../contexts/NotificationContext';

export function useUploadDocument() {
  const qc = useQueryClient();
  const { addNotification } = useNotification();

  return useMutation((form: FormData) => uploadDocument(form), {
    onSuccess: () => {
      // Invalidate search so uploaded doc shows up in search results
      // Match SearchPage.tsx query key pattern
      qc.invalidateQueries(['docs']);
      qc.invalidateQueries(['years']);
      qc.invalidateQueries(['months']);
      qc.invalidateQueries(['stats']);
      qc.invalidateQueries(['recent']);
      // Note: notification handled in UploadPage to differentiate duplicate vs new upload
    },
    onError: (error: any) => {
      const message =
        error?.response?.data?.detail || 'Gagal mengunggah dokumen. Periksa koneksi dan coba lagi.';
      addNotification(message);
      console.error('Upload error:', error);
    },
  });
}
