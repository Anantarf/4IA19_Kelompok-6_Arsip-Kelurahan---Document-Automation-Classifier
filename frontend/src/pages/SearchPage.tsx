import React, { useState, useEffect, useRef } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { getYears, getMonths, searchDocuments } from '../api/documents';
import { useAuth } from '../contexts/AuthContext';
import { Folder, FileText, ChevronRight, X, Search, BookOpen } from 'lucide-react';
import { Document } from '../types';
import DocumentModal from '../components/DocumentModal';
import { useDocument } from '../hooks/useDocument';
import { useDocumentActions } from '../hooks/useDocumentActions';
import { getJenisBadge } from '../utils/jenis';

// --- Types ---
type ViewLevel = 'root' | 'jenis' | 'tahun' | 'bulan';
type Breadcrumb = { label: string; value: string; level: ViewLevel };

export default function ArchivePage() {
  const location = useLocation();
  const navigate = useNavigate();
  const [path, setPath] = useState<Breadcrumb[]>([]);
  const [selectedDoc, setSelectedDoc] = useState<Document | null>(null);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [localSearch, setLocalSearch] = useState('');
  const [globalSearch, setGlobalSearch] = useState('');
  const [debouncedGlobalSearch, setDebouncedGlobalSearch] = useState('');
  const [page, setPage] = useState(1);
  const PAGE_SIZE = 30;
  const lastOpenedIdRef = useRef<number | null>(null);
  const openDocId = (location.state as { openDocId?: number } | null)?.openDocId;
  const { user } = useAuth(); // Auth Context

  const { data: openedDoc } = useDocument(openDocId ?? null, Boolean(openDocId));

  useEffect(() => {
    setConfirmDelete(false);
  }, [selectedDoc?.id]);

  // Debounce global search untuk performa lebih baik
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedGlobalSearch(globalSearch);
    }, 300); // Tunggu 300ms setelah user berhenti mengetik

    return () => clearTimeout(timer);
  }, [globalSearch]);

  // Helper to get current context
  const currentLevel =
    path.length === 0
      ? 'root'
      : path.length === 1
        ? 'jenis'
        : path.length === 2
          ? 'tahun'
          : 'bulan';

  const currentJenis = path.find((p) => p.level === 'jenis')?.value;
  const currentTahun = path.find((p) => p.level === 'tahun')?.value;
  const currentBulan = path.find((p) => p.level === 'bulan')?.value;

  useEffect(() => {
    if (!openDocId || !openedDoc) return;
    if (lastOpenedIdRef.current === openDocId) return;
    lastOpenedIdRef.current = openDocId;

    const nextPath: Breadcrumb[] = [];
    if (openedDoc.jenis) {
      nextPath.push({
        label:
          openedDoc.jenis === 'masuk'
            ? 'Surat Masuk'
            : openedDoc.jenis === 'keluar'
              ? 'Surat Keluar'
              : 'Dokumen Lain',
        value: openedDoc.jenis,
        level: 'jenis',
      });
    }
    if (openedDoc.tahun) {
      nextPath.push({
        label: String(openedDoc.tahun),
        value: String(openedDoc.tahun),
        level: 'tahun',
      });
    }
    if (openedDoc.bulan) {
      nextPath.push({ label: openedDoc.bulan, value: openedDoc.bulan, level: 'bulan' });
    }

    setPath(nextPath);
    setLocalSearch('');
    setGlobalSearch('');
    setSelectedDoc(openedDoc as Document);
  }, [openDocId, openedDoc]);

  useEffect(() => {
    setPage(1);
  }, [currentJenis, currentTahun, currentBulan, debouncedGlobalSearch, localSearch]);

  const isGlobalSearch = debouncedGlobalSearch.trim().length > 0;

  // --- Queries ---
  const { data: years = [] } = useQuery(['years', currentJenis], () => getYears(currentJenis), {
    enabled: !isGlobalSearch && currentLevel === 'jenis' && !!currentJenis,
    staleTime: 60_000,
    refetchOnWindowFocus: false,
  });

  const { data: months = [] } = useQuery(
    ['months', currentTahun, currentJenis],
    () => getMonths(Number(currentTahun), currentJenis!),
    {
      enabled: !isGlobalSearch && currentLevel === 'tahun' && !!currentTahun,
      staleTime: 60_000,
      refetchOnWindowFocus: false,
    },
  );

  // Context-sensitive Docs Query - Now enabled for all levels with folder context
  const { data: documentsData, isLoading: isLoadingDocs } = useQuery(
    ['docs', currentTahun, currentJenis, currentBulan, localSearch, debouncedGlobalSearch, page],
    () =>
      searchDocuments({
        // If global search, ignore filters
        jenis: isGlobalSearch ? undefined : currentJenis,
        year: isGlobalSearch ? undefined : currentTahun,
        bulan: isGlobalSearch ? undefined : currentBulan,
        q: isGlobalSearch ? debouncedGlobalSearch : localSearch,
        limit: PAGE_SIZE,
        offset: (page - 1) * PAGE_SIZE,
      }),
    {
      enabled: isGlobalSearch || currentLevel !== 'root',
      keepPreviousData: true,
      staleTime: 10_000,
      refetchOnWindowFocus: false,
    },
  );

  const documents = documentsData?.items || [];
  const totalDocuments = documentsData?.total ?? documents.length;
  const pageCount = Math.max(1, Math.ceil(totalDocuments / PAGE_SIZE));

  const { renameDocument, deleteDocument, isDeleting } = useDocumentActions({
    onDeleted: () => setSelectedDoc(null),
  });

  // --- Navigation Handlers ---
  const handleNavigate = (item: Breadcrumb) => {
    setPath((prev) => [...prev, item]);
    setLocalSearch('');
    setSelectedDoc(null);
    setGlobalSearch(''); // Clear global search on nav
  };

  const handleBreadcrumbClick = (index: number) => {
    setPath((prev) => prev.slice(0, index + 1));
    setSelectedDoc(null);
    setGlobalSearch('');
  };

  const handleGlobalSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    setGlobalSearch(e.target.value);
    setSelectedDoc(null);
    // If user starts typing, we conceptually "leave" the folder view,
    // but we don't clear path so they can clear search to go back.
  };

  const handleRename = () => {
    if (!selectedDoc) return;
    renameDocument(selectedDoc);
  };

  const handleDeleteClick = () => {
    if (!selectedDoc) return;
    setConfirmDelete(true);
  };

  const handleDeleteConfirm = () => {
    if (!selectedDoc) return;
    deleteDocument(selectedDoc.id);
    setConfirmDelete(false);
  };

  // --- Renders ---

  // 1. Breadcrumbs
  const renderBreadcrumbs = () => {
    if (isGlobalSearch)
      return (
        <div className="flex items-center gap-2 text-sm font-medium text-slate-500 mb-6 bg-white p-3 rounded-xl border border-slate-200 shadow-sm">
          <Search size={16} className="text-primary-500" />
          <span className="text-slate-900 font-bold">
            Hasil Pencarian: "{debouncedGlobalSearch}"
          </span>
        </div>
      );

    return (
      <div className="flex items-center gap-2 text-sm font-medium text-slate-500 mb-6 bg-white p-3 rounded-xl border border-slate-200 shadow-sm overflow-x-auto">
        <button
          onClick={() => setPath([])}
          className={`p-1.5 rounded-lg hover:bg-primary-50 transition-colors ${path.length === 0 ? 'text-primary-600 bg-primary-50' : 'text-slate-500 hover:text-primary-600'}`}
          title="Arsip Dokumen"
        >
          <BookOpen size={18} className="shrink-0" />
        </button>
        {path.map((p, i) => (
          <div key={p.value} className="flex items-center gap-2 whitespace-nowrap">
            <ChevronRight size={14} className="text-slate-300 shrink-0" />
            <button
              onClick={() => (i < path.length - 1 ? handleBreadcrumbClick(i) : null)}
              className={`${i === path.length - 1 ? 'text-slate-900 font-bold pointer-events-none' : 'hover:text-primary-600 transition-colors'}`}
            >
              {p.label}
            </button>
          </div>
        ))}
      </div>
    );
  };

  // 2. Folder Views
  const renderFolders = () => {
    if (isGlobalSearch) return null; // Hide folders if searching

    if (currentLevel === 'root') {
      return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-6xl mx-auto mt-10">
          <button
            onClick={() => handleNavigate({ label: 'Surat Masuk', value: 'masuk', level: 'jenis' })}
            className="p-8 bg-blue-50 border-2 border-blue-100 rounded-2xl shadow-sm hover:bg-blue-100 hover:border-blue-300 hover:shadow-md transition-all group text-left"
          >
            <div className="w-16 h-16 bg-blue-600 text-white rounded-2xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform shadow-md">
              <Folder size={32} fill="currentColor" className="opacity-90" />
            </div>
            <h3 className="text-xl font-bold text-blue-900">Surat Masuk</h3>
            <p className="text-blue-700 mt-1 text-sm">Dokumen dari instansi luar</p>
          </button>
          <button
            onClick={() =>
              handleNavigate({ label: 'Surat Keluar', value: 'keluar', level: 'jenis' })
            }
            className="p-8 bg-slate-50 border-2 border-slate-100 rounded-2xl shadow-sm hover:bg-slate-100 hover:border-slate-300 hover:shadow-md transition-all group text-left"
          >
            <div className="w-16 h-16 bg-slate-700 text-white rounded-2xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform shadow-md">
              <Folder size={32} fill="currentColor" className="opacity-90" />
            </div>
            <h3 className="text-xl font-bold text-slate-900">Surat Keluar</h3>
            <p className="text-slate-600 mt-1 text-sm">Dokumen internal</p>
          </button>
          <button
            onClick={() =>
              handleNavigate({ label: 'Dokumen Lain', value: 'lainnya', level: 'jenis' })
            }
            className="p-8 bg-slate-50 border-2 border-slate-200 rounded-2xl shadow-sm hover:bg-slate-100 hover:border-slate-300 hover:shadow-md transition-all group text-left col-span-1 md:col-span-2 lg:col-span-1"
          >
            <div className="w-16 h-16 bg-slate-500 text-white rounded-2xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform shadow-md">
              <Folder size={32} fill="currentColor" className="opacity-90" />
            </div>
            <h3 className="text-xl font-bold text-slate-900">Dokumen Lain</h3>
            <p className="text-slate-600 mt-1 text-sm">Dokumen umum lainnya</p>
          </button>
        </div>
      );
    }

    if (currentLevel === 'jenis') {
      if (years.length === 0) return <EmptyState msg="Belum ada dokumen per tahun" />;
      return (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
          {years.map((y) => (
            <button
              key={y}
              onClick={() => handleNavigate({ label: String(y), value: String(y), level: 'tahun' })}
              className="flex flex-col items-center justify-center p-6 bg-white border border-slate-200 rounded-xl hover:border-primary-400 hover:shadow-md transition-all group"
            >
              <Folder
                size={48}
                className="text-primary-200 fill-primary-50 group-hover:text-primary-500 group-hover:fill-primary-100 transition-colors"
              />
              <span className="mt-3 font-semibold text-slate-700 group-hover:text-primary-700">
                {y}
              </span>
            </button>
          ))}
        </div>
      );
    }

    if (currentLevel === 'tahun') {
      if (months.length === 0) return <EmptyState msg="Belum ada dokumen per bulan" />;
      return (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
          {months.map((m) => (
            <button
              key={m}
              onClick={() => handleNavigate({ label: m, value: m, level: 'bulan' })}
              className="flex flex-col items-center justify-center p-6 bg-white border border-slate-200 rounded-xl hover:border-blue-400 hover:shadow-md transition-all group"
            >
              <Folder
                size={48}
                className="text-slate-300 fill-slate-50 group-hover:text-blue-500 group-hover:fill-blue-100 transition-colors"
              />
              <span className="mt-3 font-semibold text-slate-700 group-hover:text-blue-700">
                {m}
              </span>
            </button>
          ))}
        </div>
      );
    }

    return null;
  };

  // 3. File List View (only shown at bulan level or Global Search)
  const renderFiles = () => {
    // If a document is selected, show full modal preview
    if (selectedDoc) {
      return (
        <DocumentModal
          doc={selectedDoc}
          onClose={() => {
            setSelectedDoc(null);
            if (openDocId) {
              navigate('/search', { replace: true, state: null });
            }
          }}
          onRename={user?.role === 'admin' ? handleRename : undefined}
          onDelete={user?.role === 'admin' ? handleDeleteClick : undefined}
          onConfirmDelete={handleDeleteConfirm}
          confirmDelete={confirmDelete}
          onConfirmDeleteChange={setConfirmDelete}
          isDeleting={isDeleting}
          canEdit={user?.role === 'admin'}
          canDelete={user?.role === 'admin'}
        />
      );
    }

    // Show files ONLY at bulan level (most specific folder) OR during global search
    if (!isGlobalSearch && currentLevel !== 'bulan') return null;

    // DOCUMENT LIST - Show when at bulan level or global search (no document selected)
    return (
      <div className="w-full">
        {isLoadingDocs ? (
          <div className="text-center py-12 text-slate-500">Sedang memuat dokumen...</div>
        ) : documents.length === 0 ? (
          <div className="text-center py-12 text-slate-500">
            {isGlobalSearch ? 'Tidak ada hasil' : 'Belum ada dokumen'}
          </div>
        ) : (
          <div className="max-h-[60vh] overflow-y-auto pr-1">
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
              {documents.map((d) => (
                <button
                  key={d.id}
                  onClick={() => setSelectedDoc(d)}
                  className="p-4 bg-white border border-slate-200 rounded-xl shadow-sm hover:border-blue-400 hover:shadow-md transition-all text-left group"
                >
                  <div className="flex items-start gap-3">
                    <div className="p-2 bg-blue-50 rounded-lg text-blue-600 shrink-0 group-hover:bg-blue-100 transition-colors">
                      <FileText size={20} />
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="font-semibold text-slate-900 text-sm truncate group-hover:text-blue-600 transition-colors">
                        {d.original_filename ||
                          (d.jenis === 'masuk' ? d.perihal : undefined) ||
                          'Tanpa Nama'}
                      </p>
                      {d.jenis !== 'lainnya' && (
                        <p className="text-xs text-slate-600 mt-1 truncate">
                          {d.nomor_surat || 'Nomor belum ada'}
                        </p>
                      )}
                      <p className="text-xs text-slate-500 mt-0.5">
                        {d.tanggal_surat || 'Tanggal belum ada'}
                      </p>
                      {isGlobalSearch && (
                        <span
                          className={`inline-block mt-2 px-2 py-1 rounded text-[10px] uppercase tracking-wide font-semibold ${
                            getJenisBadge(d.jenis).className
                          }`}
                        >
                          {getJenisBadge(d.jenis).label}
                        </span>
                      )}
                    </div>
                  </div>
                </button>
              ))}
            </div>
            {totalDocuments > PAGE_SIZE && (
              <div className="flex flex-col sm:flex-row items-center justify-between gap-3 mt-6 px-1">
                <p className="text-xs text-slate-500">
                  Menampilkan {Math.min((page - 1) * PAGE_SIZE + 1, totalDocuments)}–
                  {Math.min(page * PAGE_SIZE, totalDocuments)} dari {totalDocuments} dokumen
                </p>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={page <= 1}
                    className="px-3 py-1.5 text-xs font-semibold rounded-lg border border-slate-200 text-slate-600 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-slate-50"
                  >
                    Sebelumnya
                  </button>
                  <span className="text-xs font-semibold text-slate-600">
                    Hal {page} / {pageCount}
                  </span>
                  <button
                    onClick={() => setPage((p) => Math.min(pageCount, p + 1))}
                    disabled={page >= pageCount}
                    className="px-3 py-1.5 text-xs font-semibold rounded-lg border border-slate-200 text-slate-600 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-slate-50"
                  >
                    Berikutnya
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    );
  };

  const EmptyState = ({ msg }: { msg: string }) => (
    <div className="flex flex-col items-center justify-center py-20 text-slate-400">
      <Folder size={64} className="opacity-20 mb-4" />
      <p className="text-lg font-medium">{msg}</p>
    </div>
  );

  return (
    <div className="h-[calc(100vh-8rem)] flex flex-col animate-fade-in max-w-7xl mx-auto">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-6 gap-4">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 tracking-tight">Arsip Dokumen</h1>
          <p className="text-slate-600 text-sm mt-2 font-normal leading-relaxed">
            Kelola surat masuk dan keluar.
          </p>
        </div>

        {/* Global Search Box */}
        <div className="relative w-full sm:w-80">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
          <input
            type="text"
            placeholder="Cari dokumen..."
            className="w-full pl-12 pr-12 py-3 bg-white border border-slate-200 rounded-xl shadow-sm focus:ring-2 focus:ring-blue-200 focus:border-blue-400 transition-all text-sm font-medium hover:border-slate-300"
            value={globalSearch}
            onChange={handleGlobalSearch}
          />
          {isGlobalSearch && (
            <button
              onClick={() => setGlobalSearch('')}
              className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 p-1 rounded-md transition-colors"
            >
              <X size={16} />
            </button>
          )}
        </div>
      </div>

      <div className="flex flex-col flex-1 overflow-hidden">
        {renderBreadcrumbs()}

        <div className="flex-1 overflow-y-auto min-h-0 rounded-2xl space-y-6">
          {/* Show folders if not in global search mode */}
          {!isGlobalSearch && renderFolders()}

          {/* Show files if at bulan level or in global search */}
          {renderFiles()}
        </div>
      </div>
    </div>
  );
}
