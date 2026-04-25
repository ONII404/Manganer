import React, { useRef, useEffect } from 'react'
import { cn } from '@/lib/utils'
import { Terminal, Play, Pause, Trash2 } from 'lucide-react'

interface LiveLogsProps {
  logs: string[]
  isStreaming: boolean
  onToggleStream: () => void
  onClear: () => void
  maxHeight?: string
}

export function LiveLogs({ 
  logs, 
  isStreaming, 
  onToggleStream, 
  onClear,
  maxHeight = '400px'
}: LiveLogsProps) {
  const containerRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom when new logs arrive
  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight
    }
  }, [logs])

  const getLogLevel = (line: string): 'info' | 'warning' | 'error' | 'debug' => {
    if (line.includes('ERROR') || line.includes('❌')) return 'error'
    if (line.includes('WARN') || line.includes('⚠️')) return 'warning'
    if (line.includes('DEBUG')) return 'debug'
    return 'info'
  }

  return (
    <div className="card p-0 overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-border bg-surfaceHighlight">
        <div className="flex items-center gap-2">
          <Terminal className="w-4 h-4 text-textMuted" />
          <span className="text-sm font-medium">Logs en Vivo</span>
          <span className={cn(
            'w-2 h-2 rounded-full',
            isStreaming ? 'bg-success animate-pulse' : 'bg-textMuted'
          )} />
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={onToggleStream}
            className="p-1.5 rounded hover:bg-surfaceHighlight transition-colors"
            title={isStreaming ? 'Pausar' : 'Reanudar'}
          >
            {isStreaming ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
          </button>
          <button
            onClick={onClear}
            className="p-1.5 rounded hover:bg-surfaceHighlight transition-colors text-error"
            title="Limpiar"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Log Container */}
      <div
        ref={containerRef}
        className="font-mono text-xs p-4 overflow-auto"
        style={{ maxHeight, backgroundColor: '#0d0d12' }}
      >
        {logs.length === 0 ? (
          <div className="text-textMuted italic">Esperando logs...</div>
        ) : (
          logs.map((line, i) => {
            const level = getLogLevel(line)
            return (
              <div
                key={i}
                className={cn(
                  'py-0.5',
                  level === 'error' && 'text-error',
                  level === 'warning' && 'text-warning',
                  level === 'debug' && 'text-textMuted',
                  level === 'info' && 'text-text'
                )}
              >
                {line}
              </div>
            )
          })
        )}
      </div>
    </div>
  )
}