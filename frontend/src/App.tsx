// src/App.tsx - Sección de queries corregida
import { useState, useEffect, useCallback } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Layout } from './components/Layout'
import { LibraryTable, type MangaFile } from './components/LibraryTable'
import { TaskProgress, type TaskProgress as TaskProgressData } from './components/TaskProgress'
import { LiveLogs } from './components/LiveLogs'
import { MetricsDashboard } from './components/MetricsDashboard'
import { useFiles } from './hooks/useFiles'
import { useTaskSSE } from './hooks/useTaskSSE'
import { useTasks } from './hooks/useTasks'
import { api, type HealthResponse, type FileListResponse } from './lib/api'

export default function App() {
  const [activeTab, setActiveTab] = useState('library')
  const [logs, setLogs] = useState<string[]>([])
  const [isStreamingLogs, setIsStreamingLogs] = useState(true)
  const [activeTaskId, setActiveTaskId] = useState<string | null>(null)
  
  const { submitTask, trackTask, activeTasks } = useTasks()
  const { progress: taskProgress } = useTaskSSE(activeTaskId)
  
  // ✅ CORRECTO: Desestructurar 'data' y renombrar localmente
  const { 
    data: health,           // ✅ health = HealthResponse | undefined
    isLoading: healthLoading,
    error: healthError
  } = useQuery<HealthResponse, Error>({
    queryKey: ['health'],
    queryFn: () => api.getHealth(),
    refetchInterval: 30_000,
    retry: 2,
  })
  
  // ✅ CORRECTO: useFiles retorna UseQueryResult<FileListResponse>
  // Desestructurar 'data' y renombrar a 'filesData'
  const [searchQuery, setSearchQuery] = useState('')
  const { 
    data: filesData,        // ✅ filesData = FileListResponse | undefined
    isLoading: filesLoading, 
    error: filesError 
  } = useFiles({
    limit: 1000,
    search: searchQuery || undefined,
  })
  
  // Simular logs en vivo
  useEffect(() => {
    if (!isStreamingLogs) return
    const interval = setInterval(() => {
      const levels = ['INFO', 'DEBUG', 'WARN']
      const messages = [
        'Escaneando biblioteca...',
        `Procesando ${filesData?.files?.length || 0} archivos`,
        'Hash calculado correctamente',
        'Tarea completada',
        'Conexión Redis estable',
        `Espacio libre: ${health?.storage?.free_gb ?? '—'} GB`,
      ]
      const line = `[${new Date().toLocaleTimeString()}] ${levels[Math.floor(Math.random() * levels.length)]}: ${messages[Math.floor(Math.random() * messages.length)]}`
      setLogs(prev => [...prev.slice(-99), line])
    }, 3000)
    return () => clearInterval(interval)
  }, [isStreamingLogs, filesData?.files?.length, health?.storage?.free_gb])
  
  // Manejar tarea de prueba
  const handleTestTask = useCallback(async () => {
    try {
      const taskId: string = await submitTask([{ name: 'test-file.cbz' }])
      setActiveTaskId(taskId)
      setLogs(prev => [...prev, `[${new Date().toLocaleTimeString()}] INFO: Tarea iniciada: ${taskId}`])
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Unknown error'
      setLogs(prev => [...prev, `[${new Date().toLocaleTimeString()}] ERROR: ${msg}`])
    }
  }, [submitTask])
  
  // Actualizar logs con progreso de tarea
  useEffect(() => {
    if (!taskProgress) return
    const msg = `[${new Date().toLocaleTimeString()}] ${taskProgress.status.toUpperCase()}: ${taskProgress.current || ''} (${taskProgress.progress}%)`
    setLogs(prev => {
      if (prev[prev.length - 1]?.includes(taskProgress.task_id)) {
        return [...prev.slice(0, -1), msg]
      }
      return [...prev.slice(-99), msg]
    })
  }, [taskProgress])
  
  const renderContent = () => {
    switch (activeTab) {
      case 'library':
        if (filesLoading) {
          return <div className="card flex items-center justify-center h-64">Cargando biblioteca...</div>
        }
        if (filesError) {
          return (
            <div className="card border-error/20 bg-error/5 p-4">
              <p className="text-error font-medium">Error al cargar archivos</p>
              <p className="text-sm text-textMuted mt-1">{filesError.message}</p>
              <button 
                onClick={() => window.location.reload()}
                className="btn btn-secondary mt-3"
              >
                Reintentar
              </button>
            </div>
          )
        }
        return (
          <div className="space-y-4">
            <div className="flex gap-2">
              <input
                type="text"
                placeholder="Buscar por título, autor..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="input flex-1"
              />
              <button 
                onClick={() => setSearchQuery('')}
                className="btn btn-secondary"
                disabled={!searchQuery}
              >
                Limpiar
              </button>
            </div>
            
            {/* ✅ filesData.files es MangaFile[] (con optional chaining) */}
            <LibraryTable 
              files={filesData?.files || []} 
              isLoading={filesLoading}
            />
            
            {filesData && (
              <div className="text-xs text-textMuted text-center">
                Mostrando {filesData.files.length} de {filesData.total} archivos
              </div>
            )}
          </div>
        )
      
      case 'tasks':
        return (
          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <button onClick={handleTestTask} className="btn btn-primary" disabled={!!activeTaskId}>
                {activeTaskId ? 'Tarea en progreso...' : 'Ejecutar Tarea de Prueba'}
              </button>
              <span className="text-sm text-textMuted">
                {activeTasks.size + (activeTaskId ? 1 : 0)} tarea(s) activa(s)
              </span>
            </div>
            
            {activeTaskId && taskProgress && (
              <TaskProgress task={taskProgress} />
            )}
            
            {Array.from(activeTasks.values()).map(task => (
              <TaskProgress key={task.task_id} task={task} />
            ))}
            
            {activeTasks.size === 0 && !activeTaskId && (
              <div className="card text-center py-8 text-textMuted">
                No hay tareas en ejecución
              </div>
            )}
          </div>
        )
      
      case 'metrics':
        return (
          <MetricsDashboard 
            health={health || null} 
            isLoading={healthLoading}
            fileCount={filesData?.total || 0}
            spaceSaved="2.4 GB"
          />
        )
      
      case 'settings':
        return (
          <div className="card">
            <h3 className="font-medium mb-4">Configuración</h3>
            <div className="space-y-4 text-sm">
              <div className="flex items-center justify-between py-2 border-b border-border">
                <span>Directorio de datos</span>
                <code className="text-xs bg-surfaceHighlight px-2 py-1 rounded">/app/data</code>
              </div>
              <div className="flex items-center justify-between py-2 border-b border-border">
                <span>Workers Celery</span>
                <span className="font-mono">{health?.workers || 4}</span>
              </div>
              <div className="flex items-center justify-between py-2 border-b border-border">
                <span>Modo OPDS</span>
                <span className={health?.status === 'ok' ? 'text-success' : 'text-warning'}>
                  {health?.status === 'ok' ? 'Público' : 'Privado'}
                </span>
              </div>
              <div className="flex items-center justify-between py-2">
                <span>Estado del Backend</span>
                <span className={`flex items-center gap-2 ${health?.status === 'ok' ? 'text-success' : 'text-error'}`}>
                  <span className={`w-2 h-2 rounded-full ${health?.status === 'ok' ? 'bg-success' : 'bg-error'}`} />
                  {health?.status === 'ok' ? 'Conectado' : 'Desconectado'}
                </span>
              </div>
            </div>
          </div>
        )
      
      default:
        return null
    }
  }

  return (
    <Layout activeTab={activeTab} onTabChange={setActiveTab}>
      <div className="space-y-6">
        {renderContent()}
        <LiveLogs
          logs={logs}
          isStreaming={isStreamingLogs}
          onToggleStream={() => setIsStreamingLogs(!isStreamingLogs)}
          onClear={() => setLogs([])}
          maxHeight="300px"
        />
      </div>
    </Layout>
  )
}