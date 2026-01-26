import { useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../api/axios';
import { useNotification } from '../contexts/NotificationContext';
import type { Document } from '../types';

type UpdatePayload = { id: number; updates: Partial<Document> };

type Options = {
  onUpdated?: () => void;
  onDeleted?: () => void;
};

export function useDocumentActions(options: Options = {}) {
  const { addNotification } = useNotification();
  const qc = useQueryClient();

  const updateMutation = useMutation(
    async (data: UpdatePayload) => {
      const { id, updates } = data;
      const response = await api.patch(`/documents/${id}`, updates);
      return response.data;
    },
    {
      onSuccess: () => {
        qc.invalidateQueries(['docs']);
        qc.invalidateQueries(['stats']);
        qc.invalidateQueries(['recent']);
        addNotification('Dokumen berhasil diperbarui');
        options.onUpdated?.();
      },
      onError: (error: any) => {
        const message = error?.response?.data?.detail || 'Gagal memperbarui dokumen';
        addNotification(message);
        console.error('Update error:', error);
      },
    },
  );

  const deleteMutation = useMutation(
    async (targetId: number) => {
      await api.delete(`/documents/${targetId}`);
    },
    {
      onSuccess: () => {
        qc.invalidateQueries(['docs']);
        qc.invalidateQueries(['stats']);
        qc.invalidateQueries(['recent']);
        addNotification('Dokumen berhasil dihapus');
        options.onDeleted?.();
      },
      onError: (error: any) => {
        const message = error?.response?.data?.detail || 'Gagal menghapus dokumen';
        addNotification(message);
        console.error('Delete error:', error);
      },
    },
  );

  const renameDocument = (doc: Document) => {
    const newPerihal = prompt('Masukkan Perihal baru:', doc.perihal || '');
    if (newPerihal !== null && newPerihal !== doc.perihal) {
      updateMutation.mutate({ id: doc.id, updates: { perihal: newPerihal } });
    }
  };

  return {
    renameDocument,
    deleteDocument: (id: number) => deleteMutation.mutate(id),
    isDeleting: deleteMutation.isLoading,
    isUpdating: updateMutation.isLoading,
  };
}
