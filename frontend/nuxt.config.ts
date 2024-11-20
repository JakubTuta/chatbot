import vuetify, { transformAssetUrls } from 'vite-plugin-vuetify'

export default defineNuxtConfig({
  app: {
    head: {
      title: 'Chatbot',
    },
  },

  build: {
    transpile: ['vuetify'],
  },

  modules: [
    '@vueuse/nuxt',
    '@unocss/nuxt',
    '@pinia/nuxt',
    '@nuxtjs/color-mode',
    (_options, nuxt) => {
      nuxt.hooks.hook('vite:extendConfig', (config) => {
        // eslint-disable-next-line ts/ban-ts-comment
        // @ts-expect-error
        config.plugins.push(vuetify({ autoImport: true }))
      })
    },
  ],

  imports: {
    autoImport: true,
    dirs: [
      'stores/**',
      'constants/**',
      'utils/**',
    ],
  },

  vite: {
    vue: {
      template: {
        transformAssetUrls,
      },
    },
  },

  // runtimeConfig: {
  //   public: {
  //     APP_VERSION: process.env.npm_package_version,
  //     apiKey: process.env.API_KEY,
  //     authDomain: process.env.AUTH_DOMAIN,
  //     projectId: process.env.PROJECT_ID,
  //     storageBucket: process.env.STORAGE_BUCKET,
  //     messagingSenderId: process.env.MESSAGING_SENDER_ID,
  //     appId: process.env.APP_ID,
  //   },
  // },

  ssr: false,

  nitro: {
    static: true,
    esbuild: {
      options: {
        target: 'esnext',
      },
    },
    prerender: {
      crawlLinks: true,
      routes: ['/'],
    },
  },

  typescript: {
    strict: true,
  },

  compatibilityDate: '2024-07-18',
})
