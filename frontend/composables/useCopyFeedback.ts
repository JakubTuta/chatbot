export function useCopyFeedback(timeoutMs = 1500) {
  const copiedKey = ref<string | null>(null)
  let timer: ReturnType<typeof setTimeout> | null = null

  function copy(text: string, key = 'default') {
    navigator.clipboard.writeText(text)

    copiedKey.value = key

    if (timer)
      clearTimeout(timer)

    timer = setTimeout(() => {
      copiedKey.value = null
    }, timeoutMs)
  }

  return { copiedKey, copy }
}
