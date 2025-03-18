export default defineNuxtRouteMiddleware(async (to, _from) => {
  const accessToken = localStorage.getItem('access')

  if (!accessToken) {
    return navigateTo('/auth/login')
  }

  const authStore = useAuthStore()
  const { user } = storeToRefs(authStore)

  if (user.value) {
    return
  }

  await authStore.isTokenValid()

  if (!user.value && to.path !== '/models' && to.path !== '/auth/login' && to.path !== '/auth/register') {
    navigateTo('/auth/login')
  }
})
