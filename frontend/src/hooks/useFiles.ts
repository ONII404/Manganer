// src/hooks/useFiles.ts
import { useQuery, useInfiniteQuery } from '@tanstack/react-query'
import { api, type MangaFile, type FileListResponse } from '@/lib/api'

/**
 * Hook para listar archivos con paginación simple
 * Retorna: UseQueryResult<FileListResponse, Error>
 */
export function useFiles(params?: { limit?: number; search?: string }) {
  return useQuery<FileListResponse, Error>({
    queryKey: ['files', params],
    queryFn: () => api.getFiles({ limit: params?.limit ?? 100, search: params?.search }),
    staleTime: 30_000,
    retry: 1,
    refetchOnWindowFocus: false,
  })
}

/**
 * Hook para listar archivos con scroll infinito
 * Retorna: UseInfiniteQueryResult<InfiniteData<FileListResponse, unknown>, Error>
 * 
 * Uso en componente:
 * const {  pages, fetchNextPage, hasNextPage } = useFilesInfinite()
 * pages.flatMap(page => page.files) // Array plano de MangaFile[]
 */
export function useFilesInfinite(params?: { limit?: number }) {
  // ✅ Sin tipo de retorno explícito: TypeScript lo infiere correctamente
  return useInfiniteQuery({
    queryKey: ['files-infinite', params],
    queryFn: ({ pageParam }) => {
      const offset = typeof pageParam === 'number' ? pageParam : 0
      return api.getFiles({ limit: params?.limit ?? 50, offset })
    },
    getNextPageParam: (lastPage, pages) => {
      const nextOffset = pages.length * (params?.limit ?? 50)
      return nextOffset < lastPage.total ? nextOffset : undefined
    },
    initialPageParam: 0,
    staleTime: 30_000,
  })
}

/**
 * Hook para obtener un archivo individual por ID
 */
export function useFile(fileId: number) {
  return useQuery<MangaFile, Error>({
    queryKey: ['files', fileId],
    queryFn: async () => {
      const { files } = await api.getFiles()
      const file = files.find(f => f.id === fileId)
      if (!file) throw new Error('File not found')
      return file
    },
    enabled: !!fileId,
    staleTime: 60_000,
  })
}