import { useTheme } from 'vuetify'

const THEME_KEY = 'preferred-theme'

export function useThemeToggle() {
  const theme = useTheme()

  const isDark = computed(() => theme.global.name.value === 'dark')

  function toggleTheme() {
    const next = isDark.value
      ? 'light'
      : 'dark'
    theme.global.name.value = next
    localStorage.setItem(THEME_KEY, next)
  }

  function initTheme() {
    const saved = localStorage.getItem(THEME_KEY)
    if (saved === 'light' || saved === 'dark') {
      theme.global.name.value = saved
    }
  }

  return { isDark, toggleTheme, initTheme }
}
