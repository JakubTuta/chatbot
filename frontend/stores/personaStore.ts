import type { IPersona } from '~/models/persona'
import { mapPersona } from '~/models/persona'

export const usePersonaStore = defineStore('persona', () => {
  const personas = ref<IPersona[]>([])
  const loading = ref(false)

  const apiStore = useApiStore()
  const snackbarStore = useSnackbarStore()
  const { api } = storeToRefs(apiStore)

  const fetchPersonas = async () => {
    loading.value = true

    try {
      const response = await api.value.get('personas/')

      if (response?.status === 200) {
        personas.value = response.data.map(mapPersona)
      }
    }
    catch (error: any) {
      console.error(error)
      snackbarStore.showSnackbarError(error.response?.data?.error || 'Failed to load personas.')
    }
    finally {
      loading.value = false
    }
  }

  const createPersona = async (name: string, systemPrompt: string): Promise<IPersona | null> => {
    try {
      const response = await api.value.post('personas/', { name, system_prompt: systemPrompt })

      if (response?.status === 201) {
        const persona = mapPersona(response.data)
        personas.value = [...personas.value, persona].sort((a, b) => a.name.localeCompare(b.name))

        return persona
      }
    }
    catch (error: any) {
      console.error(error)
      snackbarStore.showSnackbarError(error.response?.data?.error || 'Failed to create persona.')
    }

    return null
  }

  const updatePersona = async (id: string, name: string, systemPrompt: string): Promise<boolean> => {
    try {
      const response = await api.value.put('personas/', { id, name, system_prompt: systemPrompt })

      if (response?.status === 200) {
        personas.value = personas.value
          .map(p => (p.id === id
            ? mapPersona(response.data)
            : p))
          .sort((a, b) => a.name.localeCompare(b.name))

        return true
      }
    }
    catch (error: any) {
      console.error(error)
      snackbarStore.showSnackbarError(error.response?.data?.error || 'Failed to update persona.')
    }

    return false
  }

  const deletePersona = async (id: string): Promise<boolean> => {
    try {
      const response = await api.value.delete('personas/', { data: { id } })

      if (response?.status === 200) {
        personas.value = personas.value.filter(p => p.id !== id)

        return true
      }
    }
    catch (error: any) {
      console.error(error)
      snackbarStore.showSnackbarError(error.response?.data?.error || 'Failed to delete persona.')
    }

    return false
  }

  return {
    personas,
    loading,
    fetchPersonas,
    createPersona,
    updatePersona,
    deletePersona,
  }
})
