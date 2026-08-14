export interface IPromptTemplate {
  id: string
  name: string
  description: string
  content: string
  created_at: string
}

export function mapPromptTemplate(data: Partial<IPromptTemplate>): IPromptTemplate {
  return {
    id: data.id?.toString() || '',
    name: data.name || '',
    description: data.description || '',
    content: data.content || '',
    created_at: data.created_at || '',
  }
}
