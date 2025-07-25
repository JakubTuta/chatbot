import type { IUser } from '~/models/user'
import { jwtDecode } from 'jwt-decode'
import { mapUser } from '~/models/user'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<IUser | null>(null)
  const loading = ref(false)

  const router = useRouter()
  const snackbarStore = useSnackbarStore()

  const apiStore = useApiStore()
  const { api } = storeToRefs(apiStore)

  const resetState = () => {
    const chatStore = useChatStore()
    const containerStore = useContainerStore()

    chatStore.resetState()
    containerStore.resetState()

    user.value = null
    loading.value = false
  }

  const clearAuth = () => {
    localStorage.removeItem(ACCESS_TOKEN)
    localStorage.removeItem(REFRESH_TOKEN)
    user.value = null
  }

  const logOut = () => {
    clearAuth()
    resetState()

    return router.push('/')
  }

  const getCurrentUser = async () => {
    const url = '/auth/user/me/'

    const response = await api.value.get(url)

    if (apiStore.isResponseOk(response)) {
      user.value = mapUser(response.data)
    }
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

      if (apiStore.isResponseOk(response)) {
        snackbarStore.showSnackbarSuccess('User logged in!')

        user.value = mapUser(response.data.user)

        const tokens = response.data.token
        localStorage.setItem(ACCESS_TOKEN, tokens.access)
        localStorage.setItem(REFRESH_TOKEN, tokens.refresh)

        if (router.currentRoute.value.path !== '/models')
          router.push('/chat')
      }
    }
    // @ts-expect-error error type
    catch (error: AxiosError) {
      snackbarStore.showSnackbarError(error.response?.data?.error || 'Error logging in!')
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

      if (apiStore.isResponseOk(response)) {
        snackbarStore.showSnackbarSuccess('User created successfully!')

        user.value = mapUser(response.data.user)

        const tokens = response.data.token
        localStorage.setItem(ACCESS_TOKEN, tokens.access)
        localStorage.setItem(REFRESH_TOKEN, tokens.refresh)

        if (router.currentRoute.value.path !== '/models')
          router.push('/chat')
      }
    }
    // @ts-expect-error error type
    catch (error: AxiosError) {
      snackbarStore.showSnackbarError(error.response?.data?.error || 'Error creating user!')
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
        getCurrentUser()
      }
      else {
        clearAuth()
      }
    }
    catch (error) {
      console.error(error)
      clearAuth()
      logOut()
    }
  }

  const isTokenValid = async () => {
    const token = localStorage.getItem(ACCESS_TOKEN)

    if (!token) {
      clearAuth()

      return false
    }

    const decodedToken = jwtDecode(token)
    const tokenExpirationDate = decodedToken.exp || 0
    const now = Date.now() / 1000

    if (tokenExpirationDate < now) {
      await refreshToken()
    }
    else {
      getCurrentUser()
    }

    return user.value !== null
  }

  const init = async () => {
    if (user.value && router.currentRoute.value.path !== '/models') {
      router.push('/chat')

      return
    }

    await getCurrentUser()

    if (!user.value)
      await refreshToken()

    if (user.value && router.currentRoute.value.path !== '/models')
      router.push('/chat')
  }

  return {
    user,
    loading,
    init,
    getCurrentUser,
    login,
    register,
    logOut,
    isTokenValid,
    refreshToken,
  }
})
