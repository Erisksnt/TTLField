// frontend/src/hooks/useWebSocket.ts
import { useEffect, useRef, useState, useCallback } from 'react'
import { useAuthStore } from '@/store/auth'

interface WebSocketMessage {
  type: 'position_update' | 'alert' | 'status_change' | 'pong'
  technician_id?: string
  data?: any
  timestamp: string
}

export function useWebSocket() {
  const [isConnected, setIsConnected] = useState(false)
  const [lastPosition, setLastPosition] = useState<Record<string, any>>({})
  const [lastAlert, setLastAlert] = useState<any>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>()
  const { token } = useAuthStore()

  const connect = useCallback(() => {
    if (!token) return

    const apiBase = import.meta.env.VITE_API_URL || 'http://localhost:8000'
    const wsBase = apiBase.replace(/^http/, 'ws')
    const wsUrl = `${wsBase}/ws/frontend/${Date.now()}?token=${encodeURIComponent(token)}`
    const ws = new WebSocket(wsUrl)
    
    ws.onopen = () => {
      console.log('✅ WebSocket conectado')
      setIsConnected(true)
      wsRef.current = ws
    }
    
    ws.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data)
        
        switch (message.type) {
          case 'position_update':
            setLastPosition(prev => ({
              ...prev,
              [message.technician_id!]: message.data
            }))
            break
          case 'alert':
            setLastAlert(message.data)
            break
          case 'status_change':
            setLastPosition(prev => ({
              ...prev,
              [message.technician_id!]: { is_online: message.data?.is_online }
            }))
            break
        }
      } catch (error) {
        console.error('Erro ao processar mensagem:', error)
      }
    }
    
    ws.onclose = () => {
      console.log('❌ WebSocket desconectado')
      setIsConnected(false)
      
      // Tentar reconectar após 3 segundos
      reconnectTimeoutRef.current = setTimeout(() => {
        connect()
      }, 3000)
    }
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
    }
  }, [token])
  
  useEffect(() => {
    connect()
    
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.close()
      }
    }
  }, [connect])
  
  const sendMessage = useCallback((message: object) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message))
    }
  }, [])
  
  return {
    isConnected,
    lastPosition,
    lastAlert,
    sendMessage
  }
}