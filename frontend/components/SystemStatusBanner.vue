<script setup lang="ts">
const containerStore = useContainerStore()

const status = ref<'checking' | 'ok' | 'docker_down' | 'backend_unreachable'>('checking')

async function check() {
  status.value = 'checking'
  status.value = await containerStore.checkSystemStatus()
}

onMounted(check)
</script>

<template>
  <div
    v-if="status === 'docker_down' || status === 'backend_unreachable'"
    class="status-banner"
  >
    <span class="status-banner-label">Docker</span>

    <span class="status-banner-text">
      <template v-if="status === 'docker_down'">
        Docker isn't running. Start Docker Desktop, wait for it to initialise, then recheck — it's
        required to run AI model containers.
      </template>

      <template v-else>
        Can't reach the backend server. This is separate from Docker — check that the Django server
        is running, then recheck.
      </template>
    </span>

    <button
      type="button"
      class="status-banner-action"
      @click="check"
    >
      Recheck
    </button>
  </div>

  <div
    v-else-if="status === 'checking'"
    class="mono-kicker"
    style="margin-bottom: 8px"
  >
    Checking system status…
  </div>
</template>
