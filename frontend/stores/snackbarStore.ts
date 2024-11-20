export const useSnackbarStore = defineStore('snackbar', () => {
  const isShow = ref(false)
  const text = ref('')
  const color = ref('')

  const showSnackbarSuccess = (title: string) => {
    isShow.value = true
    text.value = title
    color.value = 'success'
  }

  const showSnackbarError = (title: string) => {
    isShow.value = true
    text.value = title
    color.value = 'error'
  }

  return {
    isShow,
    text,
    color,
    showSnackbarSuccess,
    showSnackbarError,
  }
})
