import io, { Socket } from 'socket.io-client'

class WebSocketService {
  private socket: Socket | null = null
  private listeners: Map<string, Function[]> = new Map()
  private isConnected = false

  connect(url: string = import.meta.env.VITE_API_URL || 'http://localhost:8081'): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.socket = io(url, {
          reconnection: true,
          reconnectionDelay: 1000,
          reconnectionDelayMax: 5000,
          reconnectionAttempts: 5,
          transports: ['websocket', 'polling'],
        })

        this.socket.on('connect', () => {
          this.isConnected = true
          console.log('[WebSocket] Connected')
          this.emit('connected')
          resolve()
        })

        this.socket.on('disconnect', () => {
          this.isConnected = false
          console.log('[WebSocket] Disconnected')
          this.emit('disconnected')
        })

        this.socket.on('error', (error) => {
          console.error('[WebSocket] Error:', error)
          this.emit('error', error)
        })

        // Generic message handler
        this.socket.on('message', (data) => {
          this.emit('message', data)
        })

        // Dashboard-specific events
        this.socket.on('profit:update', (data) => {
          this.emit('profit:update', data)
        })

        this.socket.on('status:update', (data) => {
          this.emit('status:update', data)
        })

        this.socket.on('analytics:update', (data) => {
          this.emit('analytics:update', data)
        })

        this.socket.on('operations:update', (data) => {
          this.emit('operations:update', data)
        })

        this.socket.on('risk:update', (data) => {
          this.emit('risk:update', data)
        })

        this.socket.on('trading:update', (data) => {
          this.emit('trading:update', data)
        })

        this.socket.on('compliance:update', (data) => {
          this.emit('compliance:update', data)
        })
      } catch (error) {
        reject(error)
      }
    })
  }

  disconnect(): void {
    if (this.socket) {
      this.socket.disconnect()
      this.socket = null
    }
  }

  on(event: string, callback: Function): void {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, [])
    }
    this.listeners.get(event)!.push(callback)
  }

  off(event: string, callback: Function): void {
    if (this.listeners.has(event)) {
      const callbacks = this.listeners.get(event)!
      const index = callbacks.indexOf(callback)
      if (index > -1) {
        callbacks.splice(index, 1)
      }
    }
  }

  private emit(event: string, data?: any): void {
    if (this.listeners.has(event)) {
      this.listeners.get(event)!.forEach((callback) => callback(data))
    }
  }

  emit(event: string, data?: any): void {
    if (this.socket && this.isConnected) {
      this.socket.emit(event, data)
    }
  }

  isReady(): boolean {
    return this.isConnected
  }

  subscribe(channel: string): void {
    if (this.socket) {
      this.socket.emit('subscribe', { channel })
    }
  }

  unsubscribe(channel: string): void {
    if (this.socket) {
      this.socket.emit('unsubscribe', { channel })
    }
  }
}

export const websocketService = new WebSocketService()
