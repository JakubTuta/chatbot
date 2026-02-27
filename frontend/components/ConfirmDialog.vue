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
    max-width="400"
    persistent
  >
    <v-card>
      <v-card-title class="text-h6">
        {{ props.title }}
      </v-card-title>

      <v-card-text>
        {{ props.message }}
      </v-card-text>

      <v-card-actions class="justify-end">
        <v-btn
          variant="text"
          @click="emit('cancel')"
        >
          Cancel
        </v-btn>

        <v-btn
          :color="props.confirmColor || 'error'"
          variant="flat"
          @click="emit('confirm')"
        >
          {{ props.confirmLabel || 'Delete' }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>
