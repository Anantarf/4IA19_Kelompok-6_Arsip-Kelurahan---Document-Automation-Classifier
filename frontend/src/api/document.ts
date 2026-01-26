import api from "./axios";
import type { Document } from "../types";

export async function getDocument(id: number) {
  const { data } = await api.get<Document>(`/documents/${id}`);
  return data;
}

export async function getDocumentFile(id: number) {
  const { data } = await api.get(`/documents/${id}/file`, { responseType: "blob" });
  return data;
}

export async function getDocumentText(id: number) {
  const { data } = await api.get(`/documents/${id}/text`, { responseType: "text" });
  return data;
}
