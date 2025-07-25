<script setup lang="ts">
import { useSnackbarStore } from '~/stores/snackbarStore'

const snackbarStore = useSnackbarStore()
const { isShow, text, color } = storeToRefs(snackbarStore)

const timeout = ref(5000)

watch(isShow, (newValue) => {
  if (newValue) {
    setTimeout(() => {
      isShow.value = false
    }, timeout.value)
  }
})
</script>

<template>
  <v-snackbar
    :color="color || ''"
    :model-value="isShow"
    :timeout="timeout"
  >
    <div class="text-center">
      {{ text }}
    </div>
  </v-snackbar>
</template>
