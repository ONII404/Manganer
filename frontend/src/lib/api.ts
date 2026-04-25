// src/lib/api.ts
const API_BASE = '/api/v1'

export type HealthResponse = {
  status: string
  storage: { free_gb?: number; percent_used?: number; [key: string]: any }
  memory: { used_mb?: number; percent?: number; [key: string]: any }
  workers: number
  warnings?: string[]
}

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

export type FileListResponse = {
  files: MangaFile[]
  total: number
}

export type TaskSubmitRequest = { items: Array<{ name?: string; [key: string]: any }> }
export type TaskResponse = { task_id: string; status: string }

export type TaskProgress = {
  task_id: string
  status: 'queued' | 'processing' | 'completed' | 'failed'
  progress: number
  current?: string
  total?: number
  error?: string
  [key: string]: any
}

export type TaskProgressCallbacks = {
  onProgress?: (data: TaskProgress) => void
  onComplete?: (data: TaskProgress) => void
  onError?: (error: string) => void
}

export const api = {
  async getHealth(): Promise<HealthResponse> {
    const res = await fetch(`${API_BASE}/health`)
    if (!res.ok) throw new Error(`Health check failed: ${res.status}`)
    return res.json()
  },

  async getFiles(params?: { limit?: number; offset?: number; search?: string }): Promise<FileListResponse> {
    const searchParams = new URLSearchParams()
    if (params?.limit) searchParams.set('limit', params.limit.toString())
    if (params?.offset) searchParams.set('offset', params.offset.toString())
    if (params?.search) searchParams.set('search', params.search)
    
    const url = `${API_BASE}/files?${searchParams.toString()}`
    const res = await fetch(url)
    if (!res.ok) throw new Error(`Failed to fetch files: ${res.status}`)
    return res.json()
  },

  async submitTask(items: TaskSubmitRequest['items']): Promise<TaskResponse> {
    const res = await fetch(`${API_BASE}/tasks/submit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ items }),
    })
    if (!res.ok) {
      const error = await res.json().catch(() => ({ detail: 'Unknown error' }))
      throw new Error(error.detail || `Task submit failed: ${res.status}`)
    }
    return res.json()
  },

  streamTaskProgress(taskId: string, callbacks: TaskProgressCallbacks): () => void {
    const es = new EventSource(`${API_BASE}/tasks/stream/${taskId}`)
    
    es.onmessage = (event) => {
      try {
        const data: TaskProgress = JSON.parse(event.data)
        if (callbacks.onProgress) callbacks.onProgress(data)
        if (data.status === 'completed' || data.status === 'failed') {
          if (callbacks.onComplete) callbacks.onComplete(data)
          es.close()
        }
      } catch (e) {
        console.error('SSE parse error:', e)
        if (callbacks.onError) callbacks.onError('Failed to parse progress data')
      }
    }
    
    es.onerror = (err) => {
      console.error('SSE connection error:', err)
      if (callbacks.onError) callbacks.onError('Connection lost')
      es.close()
    }
    
    return () => es.close()
  },

  streamLogs(callback: (line: string) => void): () => void {
    console.warn('Log streaming not implemented yet')
    return () => {}
  },
}