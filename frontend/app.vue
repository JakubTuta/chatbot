<script setup lang="ts">
import { useThemeToggle } from '~/composables/useTheme'

const { initTheme } = useThemeToggle()
initTheme()
</script>

<template>
  <NuxtLayout>
    <v-app>
      <v-main>
        <NuxtPage />

        <Snackbar />
      </v-main>
    </v-app>
  </NuxtLayout>
</template>
