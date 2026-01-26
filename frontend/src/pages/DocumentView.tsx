import React from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useDocument } from '../hooks/useDocument';
import { useAuth } from '../contexts/AuthContext';
import DocumentModal from '../components/DocumentModal';
import { useDocumentActions } from '../hooks/useDocumentActions';
import type { Document } from '../types';

export default function DocumentView() {
  const { id } = useParams();
  const navigate = useNavigate();
  const docId = id ? Number(id) : null;
  const { data: doc, mutate } = useDocument(docId, Boolean(docId));
  const { user } = useAuth();
  const [confirmDelete, setConfirmDelete] = React.useState(false);
  const { renameDocument, deleteDocument, isDeleting } = useDocumentActions({
    onDeleted: () => navigate('/', { replace: true }),
  });

  const handleRename = () => {
    if (!doc) return;
    renameDocument(doc);
  };

  const handleDocumentUpdated = (updatedDoc: Document) => {
    mutate(updatedDoc, false); // Update the cached document data
  };

  const handleClose = () => {
    if (window.history.length > 1) {
      navigate(-1);
    } else {
      navigate('/');
    }
  };

  if (!doc) {
    return (
      <div className="flex items-center justify-center h-64 text-slate-500">Memuat dokumen...</div>
    );
  }

  return (
    <DocumentModal
      doc={doc}
      onClose={handleClose}
      onRename={user?.role === 'admin' ? handleRename : undefined}
      onDelete={user?.role === 'admin' ? () => setConfirmDelete(true) : undefined}
      onConfirmDelete={() => deleteDocument(doc.id)}
      confirmDelete={confirmDelete}
      onConfirmDeleteChange={setConfirmDelete}
      isDeleting={isDeleting}
      canEdit={user?.role === 'admin'}
      canDelete={user?.role === 'admin'}
      onDocumentUpdated={handleDocumentUpdated}
    />
  );
}
