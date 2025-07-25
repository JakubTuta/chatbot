<script setup lang="ts">
const authStore = useAuthStore()
authStore.init()
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
