<script setup lang="ts">
const props = defineProps<{
  title: string
  message: string
  confirmLabel?: string
  confirmColor?: string
}>()

const emit = defineEmits<{
  (e: 'confirm'): void
  (e: 'cancel'): void
}>()

const isOpen = defineModel<boolean>({ default: false, required: true })
</script>

<template>
  <v-dialog
    v-model="isOpen"
    max-width="440"
    persistent
    transition="dialog-rise-transition"
  >
    <v-card class="reichat-dialog">
      <div class="reichat-dialog-header">
        <span class="reichat-dialog-title">{{ props.title }}</span>
      </div>

      <v-card-text class="reichat-dialog-body">
        {{ props.message }}
      </v-card-text>

      <v-card-actions class="reichat-dialog-actions">
        <v-spacer />

        <v-btn
          variant="text"
          @click="emit('cancel')"
        >
          Cancel
        </v-btn>

        <v-btn
          :color="props.confirmColor || 'red'"
          variant="flat"
          @click="emit('confirm')"
        >
          {{ props.confirmLabel || 'Delete' }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>
