<script setup lang="ts">
const isShow = defineModel<boolean>('isShow', { default: false })

const chatStore = useChatStore()
const { loading } = storeToRefs(chatStore)

const containerStore = useContainerStore()
const { scrapeProgress } = storeToRefs(containerStore)

const minPullCount = ref(200000)

const scrapePercent = computed(() => {
  if (!scrapeProgress.value.total)
    return 0

  return Math.round((scrapeProgress.value.completed / scrapeProgress.value.total) * 100)
})

const scrapeLabel = computed(() => {
  if (!scrapeProgress.value.running)
    return ''
  if (!scrapeProgress.value.total)
    return 'Starting scrape…'

  return `Scraped ${scrapeProgress.value.completed} of ${scrapeProgress.value.total} models${scrapeProgress.value.current
    ? ` — ${scrapeProgress.value.current}`
    : ''}`
})

async function pullModels() {
  await chatStore.pullAIModels(minPullCount.value)
}
</script>

<template>
  <v-dialog
    v-model="isShow"
    max-width="600"
    :persistent="scrapeProgress.running"
  >
    <v-card>
      <v-card-title>
        Pull Models from Ollama
      </v-card-title>

      <v-card-text>
        <v-text-field
          v-model.number="minPullCount"
          label="Minimum popularity threshold"
          hint="Only models with at least this many downloads on ollama.com will be imported. Default 200 000 is a good starting point."
          persistent-hint
          :disabled="loading || scrapeProgress.running"
        />

        <v-alert
          type="info"
          variant="tonal"
          class="mt-4"
          icon="mdi-download"
        >
          Scraping ollama.com runs in the background. Live progress is shown below.
        </v-alert>

        <template v-if="scrapeProgress.running">
          <div class="text-body-2 text-medium-emphasis mt-4">
            {{ scrapeLabel }}
          </div>

          <v-progress-linear
            class="mt-2"
            :model-value="scrapePercent"
            :indeterminate="!scrapeProgress.total"
            color="primary"
            rounded
            height="8"
          />
        </template>

        <v-alert
          v-if="scrapeProgress.error"
          type="error"
          variant="tonal"
          class="mt-4"
        >
          {{ scrapeProgress.error }}
        </v-alert>
      </v-card-text>

      <v-card-actions>
        <v-btn
          color="error"
          :disabled="scrapeProgress.running"
          @click="isShow = false"
        >
          Cancel
        </v-btn>

        <v-spacer />

        <v-btn
          color="success"
          :loading="loading || scrapeProgress.running"
          :disabled="loading || scrapeProgress.running"
          @click="pullModels"
        >
          {{ scrapeProgress.running
            ? 'Scraping…'
            : 'Pull models' }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>
