import { useQuery } from "@tanstack/react-query";
import { getDocument } from "../api/document";

export function useDocument(id: number | null, enabled = true) {
  return useQuery(["document", id], () => getDocument(id as number), { enabled: Boolean(id) && enabled });
}
