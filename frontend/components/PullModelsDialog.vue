<script setup lang="ts">
const isShow = defineModel<boolean>('isShow', { default: false })

const chatStore = useChatStore()

const minPullCount = ref(200000)

function pullModels() {
  chatStore.pullAIModels(minPullCount.value)
  isShow.value = false
}
</script>

<template>
  <v-dialog
    v-model="isShow"
    max-width="600"
  >
    <v-card>
      <v-card-title>
        Pull Models from Ollama
      </v-card-title>

      <v-card-text>
        <v-text-field
          v-model.number="minPullCount"
          label="Minimum pull count from library"
        />
      </v-card-text>

      <v-card-actions>
        <v-btn
          color="error"
          @click="isShow = false"
        >
          Cancel
        </v-btn>

        <v-btn
          color="success"
          @click="pullModels"
        >
          Pull
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>
