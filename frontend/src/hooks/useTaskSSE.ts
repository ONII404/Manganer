// src/hooks/useTaskSSE.ts
import { useState, useEffect, useCallback } from 'react'
import { api, type TaskProgress } from '@/lib/api'

export function useTaskSSE(taskId: string | null) {
  const [progress, setProgress] = useState<TaskProgress | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [connected, setConnected] = useState(false)

  const connect = useCallback(() => {
    if (!taskId) return
    
    setError(null)
    setConnected(true)
    
    const cleanup = api.streamTaskProgress(taskId, {
      onProgress: (data) => {
        setProgress(data)
        if (data.status === 'completed' || data.status === 'failed') {
          setConnected(false)
        }
      },
      onError: (err) => {
        setError(err)
        setConnected(false)
      },
      onComplete: (data) => {
        setProgress(data)
        setConnected(false)
      },
    })
    
    return cleanup
  }, [taskId])

  useEffect(() => {
    if (!taskId) return
    const cleanup = connect()
    return () => {
      cleanup?.()
      setConnected(false)
    }
  }, [taskId, connect])

  return { progress, error, connected, reconnect: connect }
}