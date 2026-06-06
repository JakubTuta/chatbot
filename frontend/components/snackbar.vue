<script setup lang="ts">
import { useSnackbarStore } from '~/stores/snackbarStore'

const snackbarStore = useSnackbarStore()
const { isShow, current } = storeToRefs(snackbarStore)
</script>

<template>
  <v-snackbar
    :color="current?.color || ''"
    :model-value="isShow"
    :timeout="5000"
    location="bottom right"
    @update:model-value="(v) => {
      if (!v) snackbarStore.dismiss()
    }"
  >
    <div>
      {{ current?.text }}
    </div>

    <template #actions>
      <v-btn
        variant="text"
        icon="mdi-close"
        size="small"
        @click="snackbarStore.dismiss()"
      />
    </template>
  </v-snackbar>
</template>
