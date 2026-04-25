// src/hooks/useTasks.ts
import { useState, useCallback } from 'react'
import { api, type TaskProgress, type TaskProgressCallbacks } from '@/lib/api'

export function useTasks() {
  const [activeTasks, setActiveTasks] = useState<Map<string, TaskProgress>>(new Map())

  const submitTask = useCallback(async (items: Array<{ name?: string }>) => {
    const response = await api.submitTask(items)
    return response.task_id
  }, [])

  const trackTask = useCallback((taskId: string, onProgress: (progress: TaskProgress) => void) => {
    const callbacks: TaskProgressCallbacks = {
      onProgress: (progress) => {
        setActiveTasks((prev) => new Map(prev).set(taskId, progress))
        onProgress(progress)
      },
      onComplete: (progress) => {
        setActiveTasks((prev) => {
          const next = new Map(prev)
          next.set(taskId, progress)
          return next
        })
        onProgress(progress)
      },
      onError: (error) => {
        console.error('Task error:', error)
      },
    }
    
    const cleanup = api.streamTaskProgress(taskId, callbacks)
    return cleanup
  }, [])

  const getTask = useCallback((taskId: string) => {
    return activeTasks.get(taskId)
  }, [activeTasks])

  return { submitTask, trackTask, getTask, activeTasks }
}