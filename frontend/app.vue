<script setup lang="ts">
useAuthStore()
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
