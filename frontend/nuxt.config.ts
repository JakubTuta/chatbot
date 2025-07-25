/* eslint-disable node/prefer-global/process */
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
    '@radya/nuxt-dompurify',
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
      'components/**',
      'models/**',
    ],
  },

  vite: {
    vue: {
      template: {
        transformAssetUrls,
      },
    },
  },

  runtimeConfig: {
    public: {
      serverUrl: process.env.SERVER_URL || process.env.DOCKER === 'true'
        ? 'http://host.docker.internal:8000/'
        : 'http://localhost:8000/',
    },
  },

  ssr: false,

  nitro: {
    preset: 'node-server',
  },

  // nitro: {
  //   static: true,
  //   esbuild: {
  //     options: {
  //       target: 'esnext',
  //     },
  //   },
  //   prerender: {
  //     crawlLinks: true,
  //     routes: ['/'],
  //     failOnError: false,
  //   },
  // },

  typescript: {
    strict: true,
  },

  compatibilityDate: '2024-07-18',
})
