<script setup lang="ts">
import { useSnackbarStore } from '~/stores/snackbarStore';

const snackbarStore = useSnackbarStore()
const { isShow, text, color } = storeToRefs(snackbarStore)
</script>

<template>
  <v-snackbar
    :color="color || ''"
    :model-value="isShow"
  >
    <div class="text-center">
      {{ text }}
    </div>
  </v-snackbar>
</template>
