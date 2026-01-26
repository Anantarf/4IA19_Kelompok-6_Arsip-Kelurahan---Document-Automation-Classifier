import { useQuery } from '@tanstack/react-query';
import { searchDocuments } from '../api/documents';
import type { SearchResult, SearchParams } from '../api/documents';

export function useSearchDocuments(params: SearchParams, enabled = true) {
  return useQuery<SearchResult>(['search-docs', params], () => searchDocuments(params), { enabled });
}
