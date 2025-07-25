import type { AxiosResponse } from 'axios'
import axios from 'axios'

export const useApiStore = defineStore('api', () => {
  const runtimeConfig = useRuntimeConfig()
  const baseURL = runtimeConfig.public.serverUrl

  const api = ref(axios.create({
    baseURL,
  }))

  api.value.interceptors.request.use((config) => {
    const accessToken = localStorage.getItem(ACCESS_TOKEN)

    if (accessToken) {
      config.headers.Authorization = `Bearer ${accessToken}`
    }

    return config
  }, (error) => {
    return Promise.reject(error)
  })

  const isResponseOk = (response: AxiosResponse | null) => {
    return response !== null && response.status >= 200 && response.status < 300
  }

  return {
    api,
    isResponseOk,
  }
})
