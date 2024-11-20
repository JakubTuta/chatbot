import axios from 'axios'

export const useApiStore = defineStore('api', () => {
  const baseURL = 'http://localhost:8000'

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

  return {
    api,
  }
})
