export default defineNuxtRouteMiddleware((_to, _from) => {
  const accessToken = localStorage.getItem('access')

  if (!accessToken) {
    return navigateTo('/auth/login')
  }
})
