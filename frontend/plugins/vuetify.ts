import { createVuetify } from 'vuetify'

import '@mdi/font/css/materialdesignicons.css'
import 'vuetify/styles'

export default defineNuxtPlugin((app) => {
  const vuetify = createVuetify({
    theme: {
      defaultTheme: 'dark',
      themes: {
        light: {
          dark: false,
          colors: {
            'background': '#F4F5F9',
            'surface': '#FFFFFF',
            'surface-2': '#ECEEF4',
            'primary': 'rgba(142, 147, 108, 1)',
            'secondary': 'rgba(113, 108, 147, 1)',
            'primary-transparent': 'rgba(142, 147, 108, 0.25)',
            'secondary-transparent': 'rgba(113, 108, 147, 0.25)',
            'league-blue': 'rgba(35, 167, 250, 1)',
            'league-red': 'rgba(252, 38, 38, 1)',
            'league-blue-transparent': 'rgba(35, 167, 250, 0.7)',
            'league-red-transparent': 'rgba(252, 38, 38, 0.7)',
            'chat-user': '#6366F1',
            'chat-bot': '#ECEEF4',
            'accent': '#6366F1',
            'accent-2': '#818CF8',
          },
        },
        dark: {
          dark: true,
          colors: {
            'background': '#0E0F13',
            'surface': '#1A1C22',
            'surface-2': '#22242C',
            'primary': 'rgba(142, 147, 108, 1)',
            'secondary': 'rgba(113, 108, 147, 1)',
            'primary-transparent': 'rgba(142, 147, 108, 0.25)',
            'secondary-transparent': 'rgba(113, 108, 147, 0.25)',
            'league-blue': 'rgba(35, 167, 250, 1)',
            'league-red': 'rgba(252, 38, 38, 1)',
            'league-blue-transparent': 'rgba(35, 167, 250, 0.7)',
            'league-red-transparent': 'rgba(252, 38, 38, 0.7)',
            'chat-user': '#6366F1',
            'chat-bot': '#22242C',
            'accent': '#6366F1',
            'accent-2': '#818CF8',
          },
        },
      },
    },
    defaults: {
      VTextField: {
        variant: 'outlined',
      },
      VAutocomplete: {
        variant: 'outlined',
      },
      VSelect: {
        variant: 'outlined',
      },
      VBtn: {
        variant: 'outlined',
        rounded: 'xl',
      },
      VContainer: {
        style: 'max-width: 1200px',
      },
      VCard: {
        rounded: 'lg',
        width: '100%',
      },
      VTab: {
        rounded: 'xl',
      },
      VListItem: {
        rounded: 'lg',
      },
    },
    display: {
      mobileBreakpoint: 'sm',
    },
  })
  app.vueApp.use(vuetify)
})
