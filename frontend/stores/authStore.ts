import { jwtDecode } from 'jwt-decode'
import { useSnackbarStore } from './snackbarStore'

export const useAuthStore = defineStore('auth', () => {
  const isAuthorized = ref(false)
  const loading = ref(false)

  const router = useRouter()
  const snackbarStore = useSnackbarStore()
  const chatStore = useChatStore()

  const apiStore = useApiStore()
  const { api } = storeToRefs(apiStore)

  const resetState = () => {
    chatStore.resetState()

    isAuthorized.value = false
    loading.value = false
  }

  const setIsAuth = (value: boolean) => {
    isAuthorized.value = value
  }

  const clearAuth = () => {
    localStorage.removeItem(ACCESS_TOKEN)
    localStorage.removeItem(REFRESH_TOKEN)
    setIsAuth(false)
  }

  const logOut = () => {
    clearAuth()
    resetState()

    return router.push('/')
  }

  const login = async (username: string, password: string) => {
    const url = '/auth/login/'

    loading.value = true

    try {
      clearAuth()

      const response = await api.value.post(url, {
        username,
        password,
      })

      if (response.status === 200) {
        snackbarStore.showSnackbarSuccess('User logged in!')

        localStorage.setItem(ACCESS_TOKEN, response.data.token.access)
        localStorage.setItem(REFRESH_TOKEN, response.data.token.refresh)
        setIsAuth(true)

        router.push('/chat')
      }
    }
    catch (error) {
      snackbarStore.showSnackbarError('Error logging in!')

      console.error(error)
    }
    finally {
      loading.value = false
    }
  }

  const register = async (username: string, password: string) => {
    const url = '/auth/register/'

    loading.value = true

    try {
      clearAuth()

      const response = await api.value.post(url, {
        username,
        password,
      })

      if (response.status === 201) {
        snackbarStore.showSnackbarSuccess('User created successfully!')

        localStorage.setItem(ACCESS_TOKEN, response.data.token.access)
        localStorage.setItem(REFRESH_TOKEN, response.data.token.refresh)
        setIsAuth(true)

        router.push('/chat')
      }
    }
    catch (error) {
      snackbarStore.showSnackbarError('Error creating user!')
      console.error(error)
    }
    finally {
      loading.value = false
    }
  }

  const refreshToken = async () => {
    const refreshToken = localStorage.getItem(REFRESH_TOKEN)

    try {
      const response = await api.value.post('/auth/token/refresh/', {
        refresh: refreshToken,
      })

      if (response.status === 200) {
        localStorage.setItem(ACCESS_TOKEN, response.data.access)
        setIsAuth(true)
      }
      else {
        setIsAuth(false)
      }
    }
    catch (error) {
      console.error(error)
      setIsAuth(false)
      logOut()
    }
  }

  const auth = async () => {
    const token = localStorage.getItem(REFRESH_TOKEN)

    if (!token) {
      setIsAuth(false)

      return
    }

    const decodedToken = jwtDecode(token)
    const tokenExpirationDate = decodedToken.exp || 0
    const now = Date.now() / 1000

    if (tokenExpirationDate < now) {
      await refreshToken()
    }
    else {
      setIsAuth(true)
    }

    router.push('/chat')
  }

  const areTokensValid = async () => {
    const accessToken = localStorage.getItem(ACCESS_TOKEN)
    const refreshToken = localStorage.getItem(REFRESH_TOKEN)

    if (!accessToken || !refreshToken) {
      return false
    }

    const url = '/auth/token/check-and-refresh/'

    try {
      const response = await api.value.post(url, {
        access: accessToken,
        refresh: refreshToken,
      })

      if (response.status === 200) {
        const tokens = response.data.token

        localStorage.setItem(ACCESS_TOKEN, tokens.access)
        localStorage.setItem(REFRESH_TOKEN, tokens.refresh)

        return true
      }
    }
    catch (error) {
      console.error(error)
    }

    localStorage.removeItem(ACCESS_TOKEN)
    localStorage.removeItem(REFRESH_TOKEN)

    return false
  }

  onMounted(() => auth())

  return {
    isAuthorized,
    loading,
    login,
    register,
    logOut,
    areTokensValid,
  }
})
