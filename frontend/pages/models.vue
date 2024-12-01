<script setup lang="ts">
import type { AIModel } from '~/stores/chatStore';

const containerStore = useContainerStore()
const { containers } = storeToRefs(containerStore)

const chatStore = useChatStore()
const { aiModels } = storeToRefs(chatStore)

const selectedVersions = ref<Record<string, { parameters: string, size: string } | null>>({})
const isWindows = ref(true)
const escapeCharacter = computed(() => (isWindows.value
  ? '^'
  : '\\'))

onMounted(() => {
  containerStore.getUserContainers()
  chatStore.fetchAIModels()
})

const statusToTitle: { [key: string]: string } = {
  running: 'Running',
  exited: 'Exited',
  paused: 'Paused',
  restarting: 'Restarting',
  pulling_model: 'Pulling model',
  not_found: 'Not found',
}

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
  if (!selectedVersions.value[aiModel.model]) {
    return 'not_found'
  }

  const containerName = `${aiModel.model}_${selectedVersions.value[aiModel.model]!.parameters}`
  const container = containers.value.find(container => container.name === containerName)

  if (!container) {
    return 'not_found'
  }

  return container.status
}

function canCreateContainer(aiModel: AIModel): boolean {
  const containerStatus = findContainer(aiModel)
  const statuses = ['not_found']

  return statuses.includes(containerStatus)
}

function createContainer(aiModel: AIModel) {
  startContainer(aiModel)
}

function createContainerCommand(aiModel: AIModel): string[] {
  if (!selectedVersions.value[aiModel.model]) {
    return []
  }

  const parameters = selectedVersions.value[aiModel.model]!.parameters
  const containerName = `${aiModel.model}_${parameters}`
  const containerPort = 11434 + aiModel.id

  const createCommand = `docker run -d ${escapeCharacter.value}
  --name ${containerName} ${escapeCharacter.value}
  --network chatbot-network ${escapeCharacter.value}
  --gpus all ${escapeCharacter.value}
  -p ${containerPort}:11434 ${escapeCharacter.value}
  -e model=${aiModel.model} ${escapeCharacter.value}
  -e parameters=${parameters} ${escapeCharacter.value}
  -e port=${containerPort} ${escapeCharacter.value}
  ollama/ollama:latest`

  const pullModelCommand = `docker exec -d ${containerName} ollama pull ${aiModel.model}:${parameters}`

  return [createCommand, pullModelCommand]
}

function canStartContainer(aiModel: AIModel): boolean {
  const containerStatus = findContainer(aiModel)
  const statuses = ['exited', 'paused']

  return statuses.includes(containerStatus)
}

function startContainer(aiModel: AIModel) {
  if (!selectedVersions.value[aiModel.model]) {
    return
  }

  containerStore.runContainer({ model: aiModel.model, parameters: selectedVersions.value[aiModel.model]!.parameters })
}

function startContainerCommand(aiModel: AIModel): string[] {
  if (!selectedVersions.value[aiModel.model]) {
    return []
  }

  const parameters = selectedVersions.value[aiModel.model]!.parameters
  const containerName = `${aiModel.model}_${parameters}`

  return [`docker start ${containerName}`]
}

function canStopContainer(aiModel: AIModel): boolean {
  const containerStatus = findContainer(aiModel)
  const statuses = ['running', 'paused', 'restarting', 'pulling_model']

  return statuses.includes(containerStatus)
}

function stopContainer(aiModel: AIModel) {
  if (!selectedVersions.value[aiModel.model]) {
    return
  }

  containerStore.stopContainer({ model: aiModel.model, parameters: selectedVersions.value[aiModel.model]!.parameters })
}

function stopContainerCommand(aiModel: AIModel): string[] {
  if (!selectedVersions.value[aiModel.model]) {
    return []
  }

  const parameters = selectedVersions.value[aiModel.model]!.parameters
  const containerName = `${aiModel.model}_${parameters}`

  return [`docker stop ${containerName}`]
}

function canRemoveContainer(aiModel: AIModel): boolean {
  const containerStatus = findContainer(aiModel)
  const statuses = ['running', 'exited', 'paused', 'restarting', 'pulling_model']

  return statuses.includes(containerStatus)
}

function removeContainer(aiModel: AIModel) {
  if (!selectedVersions.value[aiModel.model]) {
    return
  }

  containerStore.removeContainer({ model: aiModel.model, parameters: selectedVersions.value[aiModel.model]!.parameters })
}

function removeContainerCommand(aiModel: AIModel): string[] {
  if (!selectedVersions.value[aiModel.model]) {
    return []
  }

  const parameters = selectedVersions.value[aiModel.model]!.parameters
  const containerName = `${aiModel.model}_${parameters}`

  const stopCommand = stopContainerCommand(aiModel)

  return stopCommand.concat([`docker remove ${containerName}`])
}

function copyToClipboard(text: string): void {
  navigator.clipboard.writeText(text)
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
              class="mt-6"
            >
              <v-row>
                <v-col
                  cols="12"
                  sm="4"
                >
                  {{ `Container status: ${statusToTitle[findContainer(aiModel)]}` }}
                </v-col>

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
              </v-row>

              <v-row>
                <!-- CREATE -->
                <v-col
                  v-if="canCreateContainer(aiModel)"
                  cols="12"
                >
                  <span class="text-h6">
                    CREATE CONTAINER
                  </span>

                  <br>

                  <br>

                  <v-btn
                    color="success"
                    @click="createContainer(aiModel)"
                  >
                    Create container
                  </v-btn>

                  <br>

                  <br>

                  <div class="mb-4">
                    Or paste these commands into the console:
                  </div>

                  <v-textarea
                    v-for="(command, index) in createContainerCommand(aiModel)"
                    :key="index"
                    append-inner-icon="mdi-content-copy"
                    readonly
                    auto-grow
                    no-resize
                    rows="1"
                    :model-value="command"
                    @click:append-inner="copyToClipboard(command)"
                  />
                </v-col>

                <!-- START -->
                <v-col
                  v-if="canStartContainer(aiModel)"
                  cols="12"
                >
                  <span class="text-h6">
                    START CONTAINER
                  </span>

                  <br>

                  <br>

                  <v-btn
                    color="success"
                    @click="startContainer(aiModel)"
                  >
                    Start container
                  </v-btn>

                  <br>

                  <br>

                  <div class="mb-4">
                    Or paste these commands into the console:
                  </div>

                  <v-textarea
                    v-for="(command, index) in startContainerCommand(aiModel)"
                    :key="index"
                    append-inner-icon="mdi-content-copy"
                    readonly
                    auto-grow
                    no-resize
                    rows="1"
                    :model-value="command"
                    @click:append-inner="copyToClipboard(command)"
                  />
                </v-col>

                <!-- STOP -->
                <v-col
                  v-if="canStopContainer(aiModel)"
                  cols="12"
                >
                  <span class="text-h6">
                    STOP CONTAINER
                  </span>

                  <br>

                  <br>

                  <v-btn
                    color="warning"
                    @click="stopContainer(aiModel)"
                  >
                    Stop container
                  </v-btn>

                  <br>

                  <br>

                  <div class="mb-4">
                    Or paste these commands into the console:
                  </div>

                  <v-textarea
                    v-for="(command, index) in stopContainerCommand(aiModel)"
                    :key="index"
                    append-inner-icon="mdi-content-copy"
                    readonly
                    auto-grow
                    no-resize
                    rows="1"
                    :model-value="command"
                    @click:append-inner="copyToClipboard(command)"
                  />
                </v-col>

                <!-- REMOVE -->
                <v-col
                  v-if="canRemoveContainer(aiModel)"
                  cols="12"
                >
                  <span class="text-h6">
                    REMOVE CONTAINER
                  </span>

                  <br>

                  <br>

                  <v-btn
                    color="error"
                    @click="removeContainer(aiModel)"
                  >
                    Remove container
                  </v-btn>

                  <br>

                  <br>

                  <div class="mb-4">
                    Or paste these commands into the console:
                  </div>

                  <v-textarea
                    v-for="(command, index) in removeContainerCommand(aiModel)"
                    :key="index"
                    append-inner-icon="mdi-content-copy"
                    readonly
                    auto-grow
                    no-resize
                    rows="1"
                    :model-value="command"
                    @click:append-inner="copyToClipboard(command)"
                  />
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
