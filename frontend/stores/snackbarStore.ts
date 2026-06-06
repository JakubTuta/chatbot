interface SnackbarItem {
  text: string
  color: string
}

export const useSnackbarStore = defineStore('snackbar', () => {
  const queue = ref<SnackbarItem[]>([])
  const current = ref<SnackbarItem | null>(null)
  const isShow = ref(false)

  function showNext() {
    if (isShow.value || queue.value.length === 0)
      return
    current.value = queue.value.shift()!
    isShow.value = true
  }

  function enqueue(item: SnackbarItem) {
    if (queue.value.length < 3)
      queue.value.push(item)
    showNext()
  }

  function dismiss() {
    isShow.value = false
    setTimeout(() => {
      current.value = null
      showNext()
    }, 300)
  }

  const showSnackbarSuccess = (text: string) => enqueue({ text, color: 'success' })
  const showSnackbarError = (text: string) => enqueue({ text, color: 'error' })
  const showSnackbarInfo = (text: string) => enqueue({ text, color: 'info' })

  return {
    isShow,
    current,
    dismiss,
    showSnackbarSuccess,
    showSnackbarError,
    showSnackbarInfo,
  }
})
