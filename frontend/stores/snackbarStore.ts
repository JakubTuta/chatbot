interface SnackbarItem {
  id: number
  text: string
  color: string
}

const AUTO_DISMISS_MS = 5000
const MAX_VISIBLE = 3

export const useSnackbarStore = defineStore('snackbar', () => {
  const toasts = ref<SnackbarItem[]>([])
  let nextId = 0

  function dismiss(id: number) {
    toasts.value = toasts.value.filter(t => t.id !== id)
  }

  function enqueue(text: string, color: string) {
    // Independent call sites often hit the same failure at once (e.g. three
    // requests each discovering Docker is down) — skip exact repeats rather
    // than stacking identical toasts.
    if (toasts.value.some(t => t.text === text))
      return

    const id = nextId++
    toasts.value.push({ id, text, color })

    // Newest is appended at the end — the stack shows at most 3 at once,
    // newest at the bottom, so a burst of toasts drops the oldest rather
    // than growing unbounded or refusing the newest.
    if (toasts.value.length > MAX_VISIBLE)
      toasts.value.shift()

    setTimeout(() => dismiss(id), AUTO_DISMISS_MS)
  }

  const showSnackbarSuccess = (text: string) => enqueue(text, 'success')
  const showSnackbarError = (text: string) => enqueue(text, 'error')
  const showSnackbarInfo = (text: string) => enqueue(text, 'info')

  return {
    toasts,
    dismiss,
    showSnackbarSuccess,
    showSnackbarError,
    showSnackbarInfo,
  }
})
