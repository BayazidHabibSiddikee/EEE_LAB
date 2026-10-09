import { useState, useEffect, useRef, useCallback } from 'react'

type ConnectionStatus = 'connecting' | 'connected' | 'disconnected' | 'error'

interface WebSocketMessage {
  type: string
  reportId?: string
  progress?: number
  status?: string
  log?: string
  path?: string
  verification?: {
    passed: boolean
    failures: number
    warnings: number
  }
  message?: string
  [key: string]: any
}

export function useWebSocket(url: string = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws') {
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null)
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('disconnected')
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const reconnectAttempts = useRef(0)
  const maxReconnectAttempts = 5

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return

    setConnectionStatus('connecting')
    
    try {
      const ws = new WebSocket(url)
      wsRef.current = ws

      ws.onopen = () => {
        setConnectionStatus('connected')
        reconnectAttempts.current = 0
        // Debug log removed for production
      }

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          setLastMessage(data)
        } catch (err) {
          console.error('[WS] Failed to parse message:', err)
        }
      }

      ws.onclose = () => {
        setConnectionStatus('disconnected')
        // Debug log removed for production
        
        // Attempt reconnect with exponential backoff
        if (reconnectAttempts.current < maxReconnectAttempts) {
          const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000)
          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectAttempts.current++
            connect()
          }, delay)
        } else {
          setConnectionStatus('error')
        }
      }

      ws.onerror = (error) => {
        console.error('[WS] Error:', error)
        setConnectionStatus('error')
      }
    } catch (err) {
      console.error('[WS] Connection failed:', err)
      setConnectionStatus('error')
    }
  }, [url])

  const sendMessage = useCallback((message: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message))
    } else {
      console.warn('[WS] Cannot send message: not connected')
    }
  }, [])

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
    }
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
    setConnectionStatus('disconnected')
  }, [])

  useEffect(() => {
    connect()
    return () => disconnect()
  }, [connect, disconnect])

  return {
    lastMessage,
    connectionStatus,
    sendMessage,
    connect,
    disconnect,
  }
}