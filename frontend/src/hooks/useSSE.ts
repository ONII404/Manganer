import { useEffect, useRef, useState } from 'react'

export function useSSE<T>(url: string, enabled: boolean = true) {
  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState<Error | null>(null)
  const [connected, setConnected] = useState(false)
  const esRef = useRef<EventSource | null>(null)

  useEffect(() => {
    if (!enabled) return

    const eventSource = new EventSource(url)
    esRef.current = eventSource

    eventSource.onopen = () => {
      setConnected(true)
      setError(null)
    }

    eventSource.onmessage = (event) => {
      try {
        const parsed = JSON.parse(event.data)
        setData(parsed)
      } catch (e) {
        setError(e instanceof Error ? e : new Error('Parse error'))
      }
    }

    eventSource.onerror = (err) => {
      setConnected(false)
      setError(err instanceof Error ? err : new Error('Connection error'))
      eventSource.close()
    }

    return () => {
      eventSource.close()
      esRef.current = null
    }
  }, [url, enabled])

  return { data, error, connected }
}