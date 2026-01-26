import api from './axios';
import type { Document } from '../types';

export type SearchResult = {
  items: Document[];
  total: number;
};

export type SearchParams = Record<string, string | number | boolean | undefined>;

export async function searchDocuments(params: SearchParams): Promise<SearchResult> {
  const res = await api.get<SearchResult>('/search/', { params });
  // Response should be array of Document[], extract total from header
  const items = Array.isArray(res.data) ? res.data : (res.data as any).items || [];
  const total = Number(res.headers['x-total-count'] ?? items.length);
  return { items, total };
}

export async function uploadDocument(formData: FormData) {
  const { data } = await api.post('/upload/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
}

export async function getYears(jenis?: string): Promise<number[]> {
  const { data } = await api.get<number[]>('/search/years', { params: { jenis } });
  return data;
}

export async function getMonths(tahun: number, jenis: string): Promise<string[]> {
  const { data } = await api.get<string[]>('/search/months', { params: { tahun, jenis } });
  return data;
}

export type DocumentUpdate = {
  nomor_surat?: string;
  perihal?: string;
  tanggal_surat?: string;
  jenis?: 'masuk' | 'keluar' | 'lainnya';
  pengirim?: string;
  penerima?: string;
  confirm_sensitive?: boolean;
};

export async function updateDocument(id: number, updates: DocumentUpdate): Promise<Document> {
  const { data } = await api.patch<Document>(`/documents/${id}`, updates);
  return data;
}
