import { useQuery } from "@tanstack/react-query";
import { getDocumentFile } from "../api/document";

export function useDocumentFile(id: number | null, enabled = true) {
  return useQuery(["document_file", id], () => getDocumentFile(id as number), { enabled: Boolean(id) && enabled });
}
