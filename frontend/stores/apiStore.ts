import type { AxiosResponse } from 'axios'
import axios from 'axios'

export const useApiStore = defineStore('api', () => {
  const runtimeConfig = useRuntimeConfig()
  const baseURL = runtimeConfig.public.serverUrl

  const api = ref(axios.create({
    baseURL,
    timeout: 15000,
  }))

  api.value.interceptors.response.use(
    response => response,
    (error) => {
      if (error.response?.status >= 500) {
        const snackbarStore = useSnackbarStore()
        snackbarStore.showSnackbarError('Server error — please try again later.')
      }
      else if (error.code === 'ECONNABORTED') {
        const snackbarStore = useSnackbarStore()
        snackbarStore.showSnackbarError('Request timed out — check your connection.')
      }
      else if (!error.response && error.code === 'ERR_NETWORK') {
        const snackbarStore = useSnackbarStore()
        snackbarStore.showSnackbarError('Network error — server may be down.')
      }

      return Promise.reject(error)
    },
  )

  const isResponseOk = (response: AxiosResponse | null) => {
    return response !== null && response.status >= 200 && response.status < 300
  }

  return {
    api,
    isResponseOk,
  }
})
