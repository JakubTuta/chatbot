export type ContainerStatus = 'running' | 'exited' | 'paused' | 'restarting' | 'pulling_model'

export interface Container {
  name: string
  status: ContainerStatus
  port: string | null
  environment: any
}

export const useContainerStore = defineStore('container', () => {
  const apiStore = useApiStore()
  const { api } = storeToRefs(apiStore)

  const containers = ref<Container[]>([])

  const resetState = () => {
    containers.value = []
  }

  const checkDockerConnection = async () => {
    const url = '/docker/'

    try {
      const response = await api.value.get(url)

      if (response.status === 200) {
        return true
      }
      else {
        return false
      }
    }
    catch (error) {
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
    catch (error) {
      console.error(error)
    }
  }

  return {
    containers,
    resetState,
    checkDockerConnection,
    getUserContainers,
  }
})
