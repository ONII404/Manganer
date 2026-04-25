// src/components/TaskProgress.tsx
import React from 'react'
import { cn } from '@/lib/utils'
import { CheckCircle, XCircle, Loader2, AlertCircle } from 'lucide-react'

export type TaskProgress = {
  task_id: string
  status: 'queued' | 'processing' | 'completed' | 'failed'
  progress: number
  current?: string
  total?: number
  error?: string
  started_at?: string
  [key: string]: any
}

export interface TaskProgressProps {
  task: TaskProgress
  compact?: boolean
}

export function TaskProgress({ task, compact = false }: TaskProgressProps) {
  const statusConfig = {
    queued: { icon: Loader2, color: 'text-warning', label: 'En cola', animate: true },
    processing: { icon: Loader2, color: 'text-primary', label: 'Procesando', animate: true },
    completed: { icon: CheckCircle, color: 'text-success', label: 'Completado', animate: false },
    failed: { icon: XCircle, color: 'text-error', label: 'Fallido', animate: false },
  }

  const config = statusConfig[task.status]
  const Icon = config.icon

  if (compact) {
    return (
      <div className="flex items-center gap-2 text-sm">
        <Icon className={cn('w-4 h-4', config.color, config.animate && 'animate-spin')} />
        <span className={cn(config.color)}>{config.label}</span>
        {task.status === 'processing' && (
          <span className="text-textMuted">• {task.progress}%</span>
        )}
      </div>
    )
  }

  return (
    <div className="card">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <Icon className={cn('w-5 h-5', config.color, config.animate && 'animate-spin')} />
          <span className="font-medium">{config.label}</span>
        </div>
        <span className="text-xs text-textMuted font-mono">{task.task_id.slice(0, 8)}...</span>
      </div>

      {task.status === 'processing' && (
        <div className="mb-3">
          <div className="flex justify-between text-xs text-textMuted mb-1">
            <span>{task.current || 'Procesando...'}</span>
            <span>{task.progress}%</span>
          </div>
          <div className="h-2 bg-surfaceHighlight rounded-full overflow-hidden">
            <div
              className="h-full bg-primary transition-all duration-300"
              style={{ width: `${task.progress}%` }}
            />
          </div>
          {task.total && (
            <div className="text-xs text-textMuted mt-1">
              {task.progress}% de {task.total} items
            </div>
          )}
        </div>
      )}

      {task.status === 'failed' && task.error && (
        <div className="flex items-start gap-2 p-3 bg-error/10 border border-error/20 rounded-md text-sm text-error">
          <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
          <span>{task.error}</span>
        </div>
      )}

      <div className="flex items-center gap-4 text-xs text-textMuted">
        {task.total && <span>{task.total} items</span>}
        {task.started_at && (
          <span>• Iniciado: {new Date(task.started_at).toLocaleTimeString()}</span>
        )}
      </div>
    </div>
  )
}