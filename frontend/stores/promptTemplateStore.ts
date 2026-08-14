import type { IPromptTemplate } from '~/models/promptTemplate'
import { mapPromptTemplate } from '~/models/promptTemplate'

export const usePromptTemplateStore = defineStore('promptTemplate', () => {
  const templates = ref<IPromptTemplate[]>([])
  const loading = ref(false)

  const apiStore = useApiStore()
  const snackbarStore = useSnackbarStore()
  const { api } = storeToRefs(apiStore)

  const fetchTemplates = async () => {
    loading.value = true

    try {
      const response = await api.value.get('prompt-templates/')

      if (response?.status === 200) {
        templates.value = response.data.map(mapPromptTemplate)
      }
    }
    catch (error: any) {
      console.error(error)
      snackbarStore.showSnackbarError(error.response?.data?.error || 'Failed to load prompt templates.')
    }
    finally {
      loading.value = false
    }
  }

  const createTemplate = async (
    name: string,
    content: string,
    description: string,
  ): Promise<IPromptTemplate | null> => {
    try {
      const response = await api.value.post('prompt-templates/', { name, content, description })

      if (response?.status === 201) {
        const template = mapPromptTemplate(response.data)
        templates.value = [...templates.value, template].sort((a, b) => a.name.localeCompare(b.name))

        return template
      }
    }
    catch (error: any) {
      console.error(error)
      snackbarStore.showSnackbarError(error.response?.data?.error || 'Failed to create prompt template.')
    }

    return null
  }

  const updateTemplate = async (
    id: string,
    name: string,
    content: string,
    description: string,
  ): Promise<boolean> => {
    try {
      const response = await api.value.put('prompt-templates/', { id, name, content, description })

      if (response?.status === 200) {
        templates.value = templates.value
          .map(t => (t.id === id
            ? mapPromptTemplate(response.data)
            : t))
          .sort((a, b) => a.name.localeCompare(b.name))

        return true
      }
    }
    catch (error: any) {
      console.error(error)
      snackbarStore.showSnackbarError(error.response?.data?.error || 'Failed to update prompt template.')
    }

    return false
  }

  const deleteTemplate = async (id: string): Promise<boolean> => {
    try {
      const response = await api.value.delete('prompt-templates/', { data: { id } })

      if (response?.status === 200) {
        templates.value = templates.value.filter(t => t.id !== id)

        return true
      }
    }
    catch (error: any) {
      console.error(error)
      snackbarStore.showSnackbarError(error.response?.data?.error || 'Failed to delete prompt template.')
    }

    return false
  }

  return {
    templates,
    loading,
    fetchTemplates,
    createTemplate,
    updateTemplate,
    deleteTemplate,
  }
})
