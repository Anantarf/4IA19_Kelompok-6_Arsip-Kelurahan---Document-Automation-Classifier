export const JENIS_BADGE = {
  masuk: { label: 'Masuk', className: 'bg-blue-50 text-blue-700' },
  keluar: { label: 'Keluar', className: 'bg-amber-50 text-amber-700' },
  lainnya: { label: 'Lain', className: 'bg-slate-100 text-slate-600' },
} as const;

export function getJenisBadge(jenis?: string | null) {
  if (!jenis) return JENIS_BADGE.lainnya;
  return JENIS_BADGE[jenis as keyof typeof JENIS_BADGE] || JENIS_BADGE.lainnya;
}

export function getJenisLabel(jenis?: string | null) {
  if (jenis === 'masuk') return 'Surat Masuk';
  if (jenis === 'keluar') return 'Surat Keluar';
  if (jenis === 'lainnya') return 'Dokumen Lain';
  return 'Dokumen Lain';
}
