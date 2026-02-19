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
            'primary': 'rgba(142, 147, 108, 1)',
            'secondary': 'rgba(113, 108, 147, 1)',
            'primary-transparent': 'rgba(142, 147, 108, 0.25)',
            'secondary-transparent': 'rgba(113, 108, 147, 0.25)',
            'league-blue': 'rgba(35, 167, 250, 1)',
            'league-red': 'rgba(252, 38, 38, 1)',
            'league-blue-transparent': 'rgba(35, 167, 250, 0.7)',
            'league-red-transparent': 'rgba(252, 38, 38, 0.7)',
          },
        },
        dark: {
          dark: true,
          colors: {
            'primary': 'rgba(142, 147, 108, 1)',
            'secondary': 'rgba(113, 108, 147, 1)',
            'primary-transparent': 'rgba(142, 147, 108, 0.25)',
            'secondary-transparent': 'rgba(113, 108, 147, 0.25)',
            'league-blue': 'rgba(35, 167, 250, 1)',
            'league-red': 'rgba(252, 38, 38, 1)',
            'league-blue-transparent': 'rgba(35, 167, 250, 0.7)',
            'league-red-transparent': 'rgba(252, 38, 38, 0.7)',
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
