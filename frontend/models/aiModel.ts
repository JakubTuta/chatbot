export interface IAIModel {
  id: string
  name: string
  model: string
  description: string
  popularity: number
  can_process_image: boolean
  versions: { parameters: string, size: string }[]
}

export function mapAIModel(data: Partial<IAIModel>): IAIModel {
  return {
    id: data.id?.toString() || '',
    name: data.name || '',
    model: data.model || '',
    description: data.description || '',
    popularity: data.popularity || 0,
    can_process_image: data.can_process_image || false,
    versions: data.versions || [],
  }
}
