import React from 'react'
import { cn, formatBytes } from '@/lib/utils'
import { HardDrive, MemoryStick, Cpu, Package } from 'lucide-react'

type HealthResponse = {
  status: string
  storage: { free_gb?: number; percent_used?: number; [key: string]: any }
  memory: { used_mb?: number; percent?: number; [key: string]: any }
  workers: number
  warnings?: string[]
}

interface MetricsDashboardProps {
  health: HealthResponse | null
  isLoading?: boolean
  fileCount?: number
  spaceSaved?: string
}

export function MetricsDashboard({ health, isLoading, fileCount = 0, spaceSaved = '0 GB' }: MetricsDashboardProps) {
  const metrics = [
    {
      label: 'Almacenamiento Libre',
      value: health?.storage?.free_gb != null ? `${health.storage.free_gb} GB` : '—',
      subtext: health?.storage?.percent_used != null ? `${health.storage.percent_used}% usado` : undefined,
      icon: HardDrive,
      color: health?.storage?.percent_used != null && health.storage.percent_used > 90 ? 'text-error' : 'text-primary',
    },
    {
      label: 'Memoria Usada',
      value: health?.memory?.used_mb != null ? `${Math.round(health.memory.used_mb)} MB` : '—',
      subtext: health?.memory?.percent != null ? `${health.memory.percent}% del total` : undefined,
      icon: MemoryStick,
      color: health?.memory?.percent != null && health.memory.percent > 80 ? 'text-warning' : 'text-success',
    },
    {
      label: 'Archivos Indexados',
      value: fileCount.toLocaleString(),
      subtext: undefined,
      icon: Package,
      color: 'text-primary',
    },
    {
      label: 'Espacio Ahorrado',
      value: spaceSaved,
      subtext: 'vía optimización',
      icon: Cpu,
      color: 'text-success',
    },
  ]

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="card animate-pulse">
            <div className="h-4 bg-surfaceHighlight rounded w-24 mb-3" />
            <div className="h-6 bg-surfaceHighlight rounded w-16 mb-1" />
            <div className="h-3 bg-surfaceHighlight rounded w-20" />
          </div>
        ))}
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {metrics.map((metric, i) => {
          const Icon = metric.icon
          return (
            <div key={i} className="card">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-textMuted">{metric.label}</span>
                <Icon className={cn('w-4 h-4', metric.color)} />
              </div>
              <div className="text-2xl font-bold">{metric.value}</div>
              {metric.subtext && (
                <div className="text-xs text-textMuted mt-1">{metric.subtext}</div>
              )}
            </div>
          )
        })}
      </div>

      {/* Workers Status */}
      {health?.workers != null && (
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-textMuted">Workers Celery</div>
              <div className="text-lg font-semibold">{health.workers} activos</div>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-success animate-pulse" />
              <span className="text-xs text-success">Operativos</span>
            </div>
          </div>
        </div>
      )}

      {/* Warnings */}
      {health?.warnings?.length != null && health.warnings.length > 0 && (
        <div className="card border-warning/20 bg-warning/5">
          <div className="flex items-start gap-2">
            <span className="text-warning font-medium">⚠️ Advertencias:</span>
            <ul className="text-sm text-textMuted list-disc list-inside">
              {health.warnings.map((w, i) => <li key={i}>{w}</li>)}
            </ul>
          </div>
        </div>
      )}
    </div>
  )
}