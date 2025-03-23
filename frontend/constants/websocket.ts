export interface WebsocketMessage {
  message: string
  ai_model: string
  ai_model_parameters: string
  image?: string
}

export interface WebsocketResponse {
  message: string
  done: boolean
}

export interface WebsocketHandlers {
  onConnect: () => void
  onDisconnect: () => void
  onSendMessage: (message: WebsocketMessage) => void
  onReceiveMessage: (data: WebsocketResponse) => void
}

export interface WebSocketWrapper extends WebSocket {
  sendMessage: (message: WebsocketMessage) => void
  closeConnection: () => void
}

export function getWebsocket(handlers: WebsocketHandlers, roomId: string): WebSocketWrapper | null {
  const runtimeConfig = useRuntimeConfig()
  const baseURL = runtimeConfig.public.serverUrl

  const url = new URL(baseURL)
  const socketHost = url.host

  const token = localStorage.getItem(ACCESS_TOKEN)

  if (!token) {
    console.warn('No access token found in local storage.')

    return null
  }

  const socket = new WebSocket(`ws://${socketHost}/ws/chat/${roomId}/?token=${token}`)

  socket.addEventListener('open', () => {
    handlers.onConnect()
  })

  socket.addEventListener('close', () => {
    handlers.onDisconnect()
  })

  socket.addEventListener('message', (event) => {
    try {
      const data = JSON.parse(event.data)
      handlers.onReceiveMessage(data)
    }
    catch (error) {
      console.error('Failed to parse WebSocket message:', error)
    }
  })

  const extendedSocket = socket as WebSocketWrapper

  extendedSocket.sendMessage = (message: WebsocketMessage) => {
    if (socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify(message))
      handlers.onSendMessage(message)
    }
    else {
      console.warn('WebSocket is not open. Message not sent:', message)
    }
  }

  extendedSocket.closeConnection = () => {
    if (socket.readyState !== WebSocket.CLOSED) {
      socket.close()
    }
  }

  return extendedSocket
}
