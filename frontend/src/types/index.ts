export type Document = {
  id: number;
  tahun: number | null;
  jenis: 'masuk' | 'keluar' | 'lainnya';
  nomor_surat?: string | null;
  perihal?: string | null;
  tanggal_surat?: string | null;
  bulan?: string | null;
  pengirim?: string | null;
  penerima?: string | null;
  stored_path: string;
  metadata_path: string;
  uploaded_at: string;
  mime_type: string;
  file_hash?: string | null;
  ocr_enabled: boolean;
  original_filename?: string | null;
};
