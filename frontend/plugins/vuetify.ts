import { createVuetify } from 'vuetify'

import '@mdi/font/css/materialdesignicons.css'
import 'vuetify/styles'

export default defineNuxtPlugin((app) => {
  const vuetify = createVuetify({
    theme: {
      defaultTheme: 'reichat',
      themes: {
        // Hex approximations of the oklch tokens in redesign/README.md —
        // Vuetify computes elevation/state-layer overlays from parsed RGB,
        // so this theme uses hex here. Raw component CSS uses the oklch
        // custom properties from assets/css/main.css directly instead.
        reichat: {
          dark: false,
          colors: {
            'background': '#eaf3ef',
            'on-background': '#26302d',
            'surface': '#fbfefd',
            'on-surface': '#26302d',
            'surface-2': '#f6fbf9',
            'soft-2': '#f1f8f5',
            'line': '#dae5e1',
            'line-2': '#e3ece9',
            'line-dash': '#cdd9d5',
            'ink-2': '#5f6b67',
            'ink-3': '#7d8985',
            'mint': '#3fc39c',
            'mint-btn': '#61d0ad',
            'mint-btn-hover': '#4bc7a2',
            'mint-tint': '#dcf1e9',
            'mint-deep': '#2a7462',
            'mint-ink': '#153c32',
            'mint-border': '#7bc4ae',
            'grey-dot': '#adb8b4',
            'primary': '#61d0ad',
            'on-primary': '#153c32',
            'amber': '#eba14a',
            'warning': '#eba14a',
            'red': '#d5504a',
            'error': '#d5504a',
          },
          variables: {
            'border-color': '#dae5e1',
            'border-opacity': 1,
          },
        },
      },
    },
    defaults: {
      VTextField: {
        variant: 'outlined',
        color: 'mint-deep',
      },
      VAutocomplete: {
        variant: 'outlined',
        color: 'mint-deep',
      },
      VSelect: {
        variant: 'outlined',
        color: 'mint-deep',
      },
      VTextarea: {
        variant: 'outlined',
        color: 'mint-deep',
      },
      VSwitch: {
        color: 'mint-btn',
      },
      VCheckbox: {
        color: 'mint-btn',
      },
      VBtn: {
        variant: 'outlined',
        rounded: 'lg',
        class: 'text-none',
      },
      VContainer: {
        style: 'max-width: 1200px',
      },
      VCard: {
        rounded: 'lg',
        width: '100%',
      },
      VTab: {
        rounded: 'lg',
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
