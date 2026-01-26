import { useQuery } from "@tanstack/react-query";
import { getDocumentText } from "../api/document";

export function useDocumentText(id: number | null, enabled = true) {
  return useQuery(["document_text", id], () => getDocumentText(id as number), { enabled: Boolean(id) && enabled });
}
