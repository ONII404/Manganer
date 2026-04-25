import React, { useMemo } from 'react'
import { useVirtualizer } from '@tanstack/react-virtual'
import { cn, formatBytes, formatDate } from '@/lib/utils'
import { FileArchive, Hash, Image as ImageIcon } from 'lucide-react'

export type MangaFile = {
  id: number
  file_path: string
  file_hash: string
  file_size: number
  file_type: 'cbz' | 'cbr'
  title?: string
  author?: string
  chapter_num?: number
  phash?: string
  created_at: string
}

interface LibraryTableProps {
  files: MangaFile[]
  isLoading?: boolean
}

export function LibraryTable({ files, isLoading }: LibraryTableProps) {
  const parentRef = React.useRef<HTMLDivElement>(null)

  const virtualizer = useVirtualizer({
    count: files.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 56, // Height per row
    overscan: 5,
  })

  const columns = useMemo(() => [
    { key: 'title', label: 'Título', width: 'flex-2' },
    { key: 'author', label: 'Autor', width: 'flex-1' },
    { key: 'type', label: 'Tipo', width: 'w-20' },
    { key: 'size', label: 'Tamaño', width: 'w-24' },
    { key: 'created', label: 'Añadido', width: 'w-28' },
  ], [])

  if (isLoading) {
    return (
      <div className="card flex items-center justify-center h-64">
        <div className="animate-pulse text-textMuted">Cargando biblioteca...</div>
      </div>
    )
  }

  if (files.length === 0) {
    return (
      <div className="card flex flex-col items-center justify-center h-64 text-center">
        <FileArchive className="w-12 h-12 text-textMuted mb-3" />
        <p className="text-textMuted">No hay archivos en la biblioteca</p>
        <p className="text-xs text-textMuted mt-1">Copia archivos .cbz o .cbr a la carpeta monitoreada</p>
      </div>
    )
  }

  return (
    <div className="card p-0 overflow-hidden">
      {/* Header */}
      <div className="flex items-center gap-2 px-4 py-3 border-b border-border bg-surfaceHighlight text-xs font-medium text-textMuted">
        {columns.map((col) => (
          <div key={col.key} className={cn(col.width === 'flex-2' ? 'flex-2' : col.width === 'flex-1' ? 'flex-1' : '')}>
            {col.label}
          </div>
        ))}
      </div>

      {/* Virtual Scroll Container */}
      <div ref={parentRef} className="h-[600px] overflow-auto">
        <div
          className="relative"
          style={{ height: `${virtualizer.getTotalSize()}px` }}
        >
          {virtualizer.getVirtualItems().map((virtualRow) => {
            const file = files[virtualRow.index]
            return (
              <div
                key={file.id}
                className={cn(
                  'absolute left-0 right-0 flex items-center gap-2 px-4 py-3 border-b border-border/50 hover:bg-surfaceHighlight transition-colors',
                  virtualRow.index % 2 === 0 ? 'bg-surface/50' : 'bg-surface'
                )}
                style={{ transform: `translateY(${virtualRow.start}px)` }}
              >
                {/* Title */}
                <div className="flex-2 min-w-0">
                  <div className="font-medium truncate">{file.title || file.file_path.split('/').pop()}</div>
                  <div className="text-xs text-textMuted truncate">{file.file_path}</div>
                </div>

                {/* Author */}
                <div className="flex-1 text-sm text-textMuted truncate">
                  {file.author || '—'}
                </div>

                {/* Type */}
                <div className="w-20">
                  <span className={cn(
                    'inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium',
                    file.file_type === 'cbz' ? 'bg-primary/20 text-primary' : 'bg-warning/20 text-warning'
                  )}>
                    <FileArchive className="w-3 h-3" />
                    {file.file_type.toUpperCase()}
                  </span>
                </div>

                {/* Size */}
                <div className="w-24 text-sm font-mono">{formatBytes(file.file_size)}</div>

                {/* Created */}
                <div className="w-28 text-xs text-textMuted">{formatDate(file.created_at)}</div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Footer */}
      <div className="px-4 py-2 border-t border-border text-xs text-textMuted flex justify-between">
        <span>{files.length} archivos</span>
        <span>{virtualizer.getVirtualItems().length} renderizados (virtual)</span>
      </div>
    </div>
  )
}