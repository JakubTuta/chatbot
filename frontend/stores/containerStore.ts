export type ContainerStatus = 'running' | 'exited' | 'paused' | 'restarting' | 'pulling_model'

export interface Container {
  name: string
  status: ContainerStatus
  port: string | null
  environment: any
}

export const useContainerStore = defineStore('container', () => {
  const apiStore = useApiStore()
  const snackbarStore = useSnackbarStore()
  const { api } = storeToRefs(apiStore)

  const containers = ref<Container[]>([])
  const loadingOperation = ref<string | null>(null)

  const resetState = () => {
    containers.value = []
    loadingOperation.value = null
  }

  const checkDockerConnection = async () => {
    const url = '/docker/'

    try {
      const response = await api.value.get(url)

      return response.status === 200
    }
    catch (error: any) {
      console.error(error)

      return false
    }
  }

  const getUserContainers = async () => {
    const url = '/docker/containers/'

    try {
      const response = await api.value.get(url)

      if (response.status === 200) {
        containers.value = response.data
      }
    }
    catch (error: any) {
      console.error(error)
      snackbarStore.showSnackbarError(error.response?.data?.error || 'Failed to load containers.')
    }
  }

  const runContainer = async (aiModel: { model: string, parameters: string }) => {
    const url = `/docker/container/${aiModel.model}?parameters=${aiModel.parameters}`
    const operationKey = `run_${aiModel.model}_${aiModel.parameters}`

    loadingOperation.value = operationKey

    try {
      const response = await api.value.post(url, {})

      if (response.status === 200) {
        await getUserContainers()
      }
    }
    catch (error: any) {
      console.error(error)
      snackbarStore.showSnackbarError(error.response?.data?.error || `Failed to start container for ${aiModel.model}.`)
    }
    finally {
      if (loadingOperation.value === operationKey)
        loadingOperation.value = null
    }
  }

  const stopContainer = async (aiModel: { model: string, parameters: string }) => {
    const url = `/docker/container/${aiModel.model}?parameters=${aiModel.parameters}&method=stop`
    const operationKey = `stop_${aiModel.model}_${aiModel.parameters}`

    loadingOperation.value = operationKey

    try {
      const response = await api.value.delete(url, {})

      if (response.status === 200) {
        await getUserContainers()
      }
    }
    catch (error: any) {
      console.error(error)
      snackbarStore.showSnackbarError(error.response?.data?.error || `Failed to stop container for ${aiModel.model}.`)
    }
    finally {
      if (loadingOperation.value === operationKey)
        loadingOperation.value = null
    }
  }

  const removeContainer = async (aiModel: { model: string, parameters: string }) => {
    const url = `/docker/container/${aiModel.model}?parameters=${aiModel.parameters}&method=remove`
    const operationKey = `remove_${aiModel.model}_${aiModel.parameters}`

    loadingOperation.value = operationKey

    try {
      const response = await api.value.delete(url, {})

      if (response.status === 200) {
        await getUserContainers()
      }
    }
    catch (error: any) {
      console.error(error)
      snackbarStore.showSnackbarError(error.response?.data?.error || `Failed to remove container for ${aiModel.model}.`)
    }
    finally {
      if (loadingOperation.value === operationKey)
        loadingOperation.value = null
    }
  }

  return {
    containers,
    loadingOperation,
    resetState,
    checkDockerConnection,
    getUserContainers,
    runContainer,
    stopContainer,
    removeContainer,
  }
})
