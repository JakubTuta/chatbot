export interface IPersona {
  id: string
  name: string
  system_prompt: string
  created_at: string
}

export function mapPersona(data: Partial<IPersona>): IPersona {
  return {
    id: data.id?.toString() || '',
    name: data.name || '',
    system_prompt: data.system_prompt || '',
    created_at: data.created_at || '',
  }
}
