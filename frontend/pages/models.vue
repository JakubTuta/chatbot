<script setup lang="ts">
import type { AIModel } from '~/stores/chatStore';

const containerStore = useContainerStore()
const { containers } = storeToRefs(containerStore)

const chatStore = useChatStore()
const { aiModels } = storeToRefs(chatStore)

const selectedVersions = ref<Record<string, { parameters: string, size: string } | null>>({})

onMounted(() => {
  containerStore.getUserContainers()
  chatStore.fetchAIModels()
})

function formatNumber(num: number): string {
  if (num >= 1000000) {
    return `${(num / 1000000).toFixed(1)}M`
  }
  else if (num >= 1000) {
    return `${(num / 1000).toFixed(1)}K`
  }
  else {
    return num.toString()
  }
}

function chipColor(value: number): string {
  if (value >= 1000000) {
    return 'blue'
  }
  else if (value >= 1000) {
    return 'green'
  }
  else {
    return 'gray'
  }
}

function findContainer(aiModel: AIModel): string {
  const container = containers.value.find(container => container.environment.model === aiModel.model)
  const containerVersion = selectedVersions.value[aiModel.model]

  if (!container || !containerVersion) {
    return 'Not found'
  }

  if (!container.environment.parameters.split(',').includes(containerVersion.parameters)) {
    return 'Not found'
  }

  return container.status
}
</script>

<template>
  <v-container>
    <v-card>
      <v-card-text>
        <v-list>
          <v-list-item
            v-for="aiModel in aiModels"
            :key="aiModel.model"
            class="mb-6"
            lines="three"
            variant="outlined"
          >
            <v-list-item-title
              class="text-h5 mb-2"
            >
              {{ aiModel.name }}

              <v-chip
                class="mb-1 ml-4"
                density="compact"
                :color="chipColor(aiModel.popularity)"
                append-icon="mdi-download"
              >
                {{ formatNumber(aiModel.popularity) }}
              </v-chip>
            </v-list-item-title>

            <v-list-item-subtitle class="text-subtitle-1">
              {{ aiModel.description }}
            </v-list-item-subtitle>

            <div
              v-if="selectedVersions[aiModel.model]"
              class="mt-4"
            >
              <v-row>
                <v-col
                  cols="12"
                  sm="4"
                >
                  {{ `Parameters: ${selectedVersions[aiModel.model]!.parameters}` }}
                </v-col>

                <v-col
                  cols="12"
                  sm="4"
                >
                  {{ `Model size: ${selectedVersions[aiModel.model]!.size}` }}
                </v-col>

                <v-col
                  cols="12"
                  sm="4"
                >
                  {{ `Container status: ${findContainer(aiModel)}` }}
                </v-col>
              </v-row>
            </div>

            <template #append>
              <v-select
                v-model="selectedVersions[aiModel.model]"
                :items="aiModel.versions"
                clearable
                label="Version"
                outlined
                class="mx-4"
                min-width="300px"
                return-object
                :item-title="item => `${item.parameters} parameters, ${item.size} size`"
              />
            </template>
          </v-list-item>
        </v-list>
      </v-card-text>
    </v-card>
  </v-container>
</template>
