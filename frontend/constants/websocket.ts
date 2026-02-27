export interface WebsocketMessage {
  message: string
  ai_model: string
  ai_model_parameters: string
  image?: string
  structured_output?: {
    field: string
    type: string
  }[]
}

export interface WebsocketResponse {
  message: string
  done: boolean
  error?: string
}

export interface WebsocketHandlers {
  onConnect: () => void
  onDisconnect: () => void
  onSendMessage: (message: WebsocketMessage) => void
  onReceiveMessage: (data: WebsocketResponse) => void
  onError?: (message: string) => void
  onReconnecting?: (attempt: number) => void
}

export interface WebSocketWrapper extends WebSocket {
  sendMessage: (message: WebsocketMessage) => void
  closeConnection: () => void
}

const RECONNECT_BASE_DELAY_MS = 1000
const RECONNECT_MAX_DELAY_MS = 30_000
const RECONNECT_MAX_ATTEMPTS = 8

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

  let reconnectAttempts = 0
  let intentionallyClosed = false
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null

  function buildSocket(): WebSocket {
    const ws = new WebSocket(`ws://${socketHost}/ws/chat/${roomId}/?token=${localStorage.getItem(ACCESS_TOKEN) || token}`)

    ws.addEventListener('open', () => {
      reconnectAttempts = 0
      handlers.onConnect()
    })

    ws.addEventListener('close', () => {
      if (intentionallyClosed)
        return

      handlers.onDisconnect()

      if (reconnectAttempts < RECONNECT_MAX_ATTEMPTS) {
        const delay = Math.min(
          RECONNECT_BASE_DELAY_MS * 2 ** reconnectAttempts,
          RECONNECT_MAX_DELAY_MS,
        )
        reconnectAttempts++

        handlers.onReconnecting?.(reconnectAttempts)

        reconnectTimer = setTimeout(() => {
          const newSocket = buildSocket()
          Object.assign(extendedSocket, newSocket)
          extendedSocket.sendMessage = (message: WebsocketMessage) => {
            if (newSocket.readyState === WebSocket.OPEN) {
              newSocket.send(JSON.stringify(message))
              handlers.onSendMessage(message)
            }
            else {
              console.warn('WebSocket is not open. Message not sent:', message)
            }
          }
          extendedSocket.closeConnection = () => {
            intentionallyClosed = true
            if (reconnectTimer)
              clearTimeout(reconnectTimer)
            if (newSocket.readyState !== WebSocket.CLOSED)
              newSocket.close()
          }
        }, delay)
      }
    })

    ws.addEventListener('message', (event) => {
      try {
        const data: WebsocketResponse = JSON.parse(event.data)

        if (data.error) {
          handlers.onError?.(data.error)
          return
        }

        handlers.onReceiveMessage(data)
      }
      catch (error) {
        console.error('Failed to parse WebSocket message:', error)
      }
    })

    return ws
  }

  const socket = buildSocket()
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
    intentionallyClosed = true
    if (reconnectTimer)
      clearTimeout(reconnectTimer)
    if (socket.readyState !== WebSocket.CLOSED)
      socket.close()
  }

  return extendedSocket
}
