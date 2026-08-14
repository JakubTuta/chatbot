import axios from 'axios'

export const useApiStore = defineStore('api', () => {
  const runtimeConfig = useRuntimeConfig()
  const baseURL = runtimeConfig.public.serverUrl

  // 30s: several Docker endpoints (checking a cold daemon, starting a
  // container) routinely take longer than a typical API timeout.
  //
  // No response interceptor here on purpose — every call site already
  // shows its own contextual error snackbar
  // (`error.response?.data?.error || 'Failed to X.'`). A generic one here
  // used to fire alongside it on every failure, burning 2 of the 3 queue
  // slots on one error.
  const api = ref(axios.create({
    baseURL,
    timeout: 30000,
  }))

  return {
    api,
  }
})
