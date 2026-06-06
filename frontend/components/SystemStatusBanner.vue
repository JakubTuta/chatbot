<script setup lang="ts">
const containerStore = useContainerStore()

const dockerStatus = ref<'checking' | 'ok' | 'error'>('checking')

onMounted(async () => {
  const ok = await containerStore.checkDockerConnection()
  dockerStatus.value = ok
    ? 'ok'
    : 'error'
})
</script>

<template>
  <v-alert
    v-if="dockerStatus === 'error'"
    type="error"
    variant="tonal"
    class="mb-4"
    icon="mdi-docker"
    prominent
  >
    <v-alert-title>Docker is not running</v-alert-title>
    Start Docker Desktop, wait for it to initialise, then refresh this page. Docker is required to run AI model containers.
  </v-alert>
</template>
