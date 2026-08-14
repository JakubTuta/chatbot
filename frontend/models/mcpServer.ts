export type MCPTransport = 'stdio' | 'http'

export interface IMCPServer {
  id: number
  name: string
  transport: MCPTransport
  command: string
  url: string
  enabled: boolean
  created_at: string
}
