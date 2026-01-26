import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import api from '../api/axios';
import {
  FileText,
  Search,
  Upload,
  ArrowRight,
  TrendingUp,
  MoreHorizontal,
  File,
  ArrowUpRight,
  ArrowDownRight,
} from 'lucide-react';
import { Document } from '../types';

export default function Dashboard() {
  const navigate = useNavigate();
  const currentDate = new Date().toLocaleDateString('id-ID', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });

  // Fetch Stats
  const { data: stats } = useQuery({
    queryKey: ['stats'],
    queryFn: async () => {
      const res = await api.get('/search/stats');
      return res.data;
    },
    placeholderData: { total_documents: 0, surat_masuk: 0, surat_keluar: 0, dokumen_lainnya: 0 },
    staleTime: 60_000,
    refetchOnWindowFocus: false,
  });

  // Fetch Activity (reuse search endpoint for now with limit 20)
  const { data: recentDocs = [] } = useQuery({
    queryKey: ['recent'],
    queryFn: async () => {
      const res = await api.get('/search/', { params: { limit: 20 } });
      // Handle both array and paginated response
      return Array.isArray(res.data) ? res.data : res.data.items || [];
    },
    staleTime: 15_000,
    refetchOnWindowFocus: false,
  });

  // Handle backend response format variations (just in case)
  const recentItems = Array.isArray(recentDocs)
    ? recentDocs
    : recentDocs?.items || recentDocs?.results || [];

  return (
    <div className="space-y-6 animate-fade-in max-w-7xl mx-auto">
      {/* Welcome Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 tracking-tight">Ringkasan Dokumen</h1>
          <p className="text-slate-600 text-sm mt-2 font-normal leading-relaxed">
            Lihat ringkasan dokumen Kelurahan Pela Mampang
          </p>
        </div>
        <div className="text-right hidden md:block">
          <p className="text-sm font-medium text-slate-500 uppercase tracking-wider">
            {currentDate}
          </p>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCardV2
          label="Total Dokumen"
          value={stats.total_documents}
          trend=""
          trendUp={true}
          icon={<FileText className="text-white" size={24} />}
          color="bg-blue-600"
        />
        <StatCardV2
          label="Surat Masuk"
          value={stats.surat_masuk}
          trend=""
          trendUp={true}
          icon={<ArrowDownRight className="text-white" size={24} />}
          color="bg-blue-600"
        />
        <StatCardV2
          label="Surat Keluar"
          value={stats.surat_keluar}
          trend=""
          trendUp={true}
          icon={<ArrowUpRight className="text-white" size={24} />}
          color="bg-slate-700"
        />
        <StatCardV2
          label="Dokumen Lain"
          value={stats.dokumen_lainnya}
          trend=""
          trendUp={true}
          icon={<File className="text-white" size={24} />}
          color="bg-slate-500"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content: Recent Files Table */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-white rounded-xl shadow-card border border-slate-100 overflow-hidden">
            <div className="p-6 border-b border-slate-100 flex items-center justify-between">
              <h3 className="font-semibold text-base sm:text-lg text-slate-900">
                Unggahan Terbaru
              </h3>
              <Link
                to="/search"
                className="text-sm text-primary-600 font-medium hover:text-primary-700 hover:underline"
              >
                Lihat Semua Dokumen
              </Link>
            </div>
            <div className="overflow-x-auto max-h-[420px] overflow-y-auto">
              <table className="w-full">
                <thead className="bg-slate-50 border-b border-slate-100">
                  <tr>
                    <th className="text-left py-3 px-6 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                      Dokumen
                    </th>
                    <th className="text-left py-3 px-6 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                      Jenis
                    </th>
                    <th className="text-left py-3 px-6 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                      Tanggal
                    </th>
                    <th className="text-right py-3 px-6 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                      Aksi
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {recentItems.length === 0 ? (
                    <tr>
                      <td colSpan={4} className="py-8 text-center text-slate-400 text-sm">
                        Belum ada dokumen baru.
                      </td>
                    </tr>
                  ) : (
                    recentItems.map((item: any) => (
                      <tr
                        key={item.id}
                        onClick={() => navigate('/search', { state: { openDocId: item.id } })}
                        className="hover:bg-slate-50 transition-colors group cursor-pointer"
                      >
                        <td className="py-4 px-6">
                          <div className="flex items-center gap-3">
                            <div className="w-8 h-8 rounded-lg bg-primary-50 text-primary-600 flex items-center justify-center">
                              <File size={16} />
                            </div>
                            <div className="max-w-[180px]">
                              <p
                                className="text-sm font-medium text-slate-900 truncate"
                                title={
                                  item.original_filename ||
                                  (item.jenis === 'masuk' ? item.perihal : undefined) ||
                                  'Dokumen'
                                }
                              >
                                {item.original_filename ||
                                  (item.jenis === 'masuk' ? item.perihal : undefined) ||
                                  'Tanpa Nama'}
                              </p>
                              {item.jenis !== 'lainnya' && (
                                <p className="text-xs text-slate-500 truncate">
                                  {item.nomor_surat || '-'}
                                </p>
                              )}
                            </div>
                          </div>
                        </td>
                        <td className="py-4 px-6">
                          <span
                            className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                              item.jenis === 'masuk'
                                ? 'bg-blue-100 text-blue-800'
                                : item.jenis === 'keluar'
                                  ? 'bg-amber-100 text-amber-800'
                                  : 'bg-slate-100 text-slate-700'
                            }`}
                          >
                            {item.jenis === 'masuk'
                              ? 'Masuk'
                              : item.jenis === 'keluar'
                                ? 'Keluar'
                                : 'Lain'}
                          </span>
                        </td>
                        <td className="py-4 px-6 text-sm text-slate-600">
                          {(item.uploaded_at || '').split('T')[0]}
                        </td>
                        <td className="py-4 px-6 text-right">
                          <Link
                            to="/search"
                            state={{ openDocId: item.id }}
                            onClick={(e) => e.stopPropagation()}
                            className="text-slate-400 hover:text-primary-600 p-1 rounded-full hover:bg-slate-100 inline-block"
                          >
                            <MoreHorizontal size={18} />
                          </Link>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Sidebar: Quick Actions & Tips */}
        <div className="space-y-6">
          {/* Quick Actions Card */}
          <div className="bg-white rounded-xl shadow-card border border-slate-100 p-6">
            <h3 className="font-semibold text-base sm:text-lg text-slate-900 mb-4">Aksi Cepat</h3>
            <div className="space-y-3">
              <Link
                to="/upload"
                className="flex items-center gap-4 p-3 rounded-lg border border-slate-200 hover:border-primary-500 hover:bg-primary-50 transition-all group cursor-pointer"
              >
                <div className="w-10 h-10 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center group-hover:bg-blue-600 group-hover:text-white transition-colors">
                  <Upload size={20} />
                </div>
                <div>
                  <p className="font-medium text-slate-900">Unggah Dokumen Baru</p>
                  <p className="text-xs text-slate-500">Pindai & Kelompokkan</p>
                </div>
              </Link>
              <Link
                to="/search"
                className="flex items-center gap-4 p-3 rounded-lg border border-slate-200 hover:border-slate-400 hover:bg-slate-50 transition-all group cursor-pointer"
              >
                <div className="w-10 h-10 rounded-full bg-slate-100 text-slate-600 flex items-center justify-center group-hover:bg-slate-700 group-hover:text-white transition-colors">
                  <Search size={20} />
                </div>
                <div>
                  <p className="font-medium text-slate-900">Cari Dokumen</p>
                  <p className="text-xs text-slate-500">Filter dokumen lama</p>
                </div>
              </Link>
            </div>
          </div>

          {/* System Status / Tips */}
          <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-xl shadow-lg p-6 text-white relative overflow-hidden border border-slate-700">
            <div className="relative z-10">
              <div className="flex items-center gap-2 mb-3">
                <div className="w-2 h-2 bg-blue-400 rounded-full animate-pulse"></div>
                <h3 className="font-semibold text-base sm:text-lg">Tips</h3>
              </div>
              <p className="text-slate-300 text-sm leading-relaxed">
                Pastikan format penamaan file konsisten untuk mempermudah pencarian otomatis oleh
                sistem.
              </p>
            </div>
            {/* Decor */}
            <div className="absolute -bottom-8 -right-8 w-32 h-32 bg-blue-500/20 rounded-full blur-2xl"></div>
          </div>
        </div>
      </div>
    </div>
  );
}

function StatCardV2({
  label,
  value,
  trend,
  trendUp,
  icon,
  color,
}: {
  label: string;
  value: string | number;
  trend: string;
  trendUp: boolean;
  icon: React.ReactNode;
  color: string;
}) {
  return (
    <div className="bg-white rounded-xl p-6 shadow-card border border-slate-100 hover:shadow-card-hover transition-all duration-300">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-slate-500">{label}</p>
          <h3 className="text-3xl font-bold text-slate-900 mt-2">{value}</h3>
        </div>
        <div className={`p-3 rounded-lg ${color} shadow-lg shadow-primary-500/20`}>{icon}</div>
      </div>
      <div className="mt-4 flex items-center text-xs">
        {trend && (
          <span className={`font-medium text-slate-400 bg-slate-50 px-2 py-1 rounded-md`}>
            {trend}
          </span>
        )}
      </div>
    </div>
  );
}
