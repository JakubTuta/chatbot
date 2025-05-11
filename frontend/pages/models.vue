<script setup lang="ts">
import type { IAIModel } from '~/models/aiModel'

const router = useRouter()

const containerStore = useContainerStore()
const { containers } = storeToRefs(containerStore)

const chatStore = useChatStore()
const { aiModels, loading } = storeToRefs(chatStore)

const snackbarStore = useSnackbarStore()

const isOpenPullModelsDialog = ref(false)
const search = ref('')
const sort = ref('popularityDecreasing')
const filter = ref('all')
const selectedVersions = ref<Record<string, { parameters: string, size: string } | null>>({})
const isWindows = ref(true)
const canProcessImages = ref(false)
const escapeCharacter = computed(() => (isWindows.value
  ? '^'
  : '\\'))

onMounted(async () => {
  const query = router.currentRoute.value.query
  if (query.search) {
    search.value = query.search as string
  }
  if (query.sort) {
    sort.value = query.sort as string
  }
  if (query.filter) {
    filter.value = query.filter as string
  }
  if (query.windows) {
    isWindows.value = query.windows === 'true'
  }
  if (query.canProcessImages) {
    canProcessImages.value = query.canProcessImages === 'true'
  }

  containerStore.getUserContainers()

  await chatStore.fetchAIModels()
})

const preparedAIModels = computed(() => {
  const searchFunction = (model: IAIModel) => {
    if (!search.value) {
      return true
    }

    return model.name.toLowerCase().includes(search.value.toLowerCase())
  }

  const sortFunction = (a: IAIModel, b: IAIModel) => {
    if (sort.value === 'popularityDecreasing') {
      return b.popularity - a.popularity
    }
    else if (sort.value === 'popularityIncreasing') {
      return a.popularity - b.popularity
    }
    else if (sort.value === 'nameAlphabetically') {
      return a.name.localeCompare(b.name)
    }
    else if (sort.value === 'nameReverseAlphabetically') {
      return b.name.localeCompare(a.name)
    }

    return 0
  }

  const filterFunction = (containerStatus: string) => {
    if (filter.value === 'all') {
      return true
    }

    if (filter.value === 'allMyModels') {
      return containerStatus !== 'not_found'
    }
    else if (filter.value === 'runningContainers') {
      return containerStatus === 'running'
    }
    else if (filter.value === 'exitedContainers') {
      return containerStatus === 'exited'
    }
    else if (filter.value === 'pausedContainers') {
      return containerStatus === 'paused'
    }
    else if (filter.value === 'restartingContainers') {
      return containerStatus === 'restarting'
    }
    else if (filter.value === 'pullingModelContainers') {
      return containerStatus === 'pulling_model'
    }
    else if (filter.value === 'notFoundContainers') {
      return containerStatus === 'not_found'
    }

    return true
  }

  const canProcessImageFunction = (model: IAIModel) => {
    return canProcessImages.value
      ? model.can_process_image
      : true
  }

  const filteredModels = aiModels.value
    .filter(searchFunction)
    .filter(canProcessImageFunction)
    .sort(sortFunction)

  const finalFilteredModels = filteredModels.map((model) => {
    const filteredVersions = model.versions.filter((version) => {
      const containerStatus = findContainerModelParameters(model, version.parameters)

      return filterFunction(containerStatus)
    })

    return { ...model, versions: filteredVersions }
  }).filter(model => model.versions.length > 0)

  return finalFilteredModels
})

const sortItems = [
  { title: 'Popularity (decreasing)', value: 'popularityDecreasing' },
  { title: 'Popularity (increasing)', value: 'popularityIncreasing' },
  { title: 'Name (alphabetically)', value: 'nameAlphabetically' },
  { title: 'Name (reverse-alphabetically)', value: 'nameReverseAlphabetically' },
]

const filterItems = [
  { title: 'All', value: 'all' },
  { title: 'All my models', value: 'allMyModels' },
  { title: 'Running containers', value: 'runningContainers' },
  { title: 'Exited containers', value: 'exitedContainers' },
  { title: 'Paused containers', value: 'pausedContainers' },
  { title: 'Restarting containers', value: 'restartingContainers' },
  { title: 'Pulling model containers', value: 'pullingModelContainers' },
  { title: 'Not found containers', value: 'notFoundContainers' },
]

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

function findContainer(aiModel: IAIModel): string {
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

function findContainerModelParameters(aiModel: IAIModel, parameters: string): string {
  const containerName = `${aiModel.model}_${parameters}`
  const container = containers.value.find(container => container.name === containerName)

  if (!container) {
    return 'not_found'
  }

  return container.status
}

function canCreateContainer(aiModel: IAIModel): boolean {
  const containerStatus = findContainer(aiModel)
  const statuses = ['not_found']

  return statuses.includes(containerStatus)
}

function createContainer(aiModel: IAIModel) {
  if (!selectedVersions.value[aiModel.model]) {
    return
  }

  containerStore.runContainer({ model: aiModel.model, parameters: selectedVersions.value[aiModel.model]!.parameters })
  snackbarStore.showSnackbarSuccess('Container is being created')
}

function createContainerCommand(aiModel: IAIModel): string[] {
  if (!selectedVersions.value[aiModel.model]) {
    return []
  }

  const parameters = selectedVersions.value[aiModel.model]!.parameters
  const containerName = `${aiModel.model}_${parameters}`
  const containerPort = 11434 + aiModel.index

  const createCommand = `docker run -d ${escapeCharacter.value}
  --name ${containerName} ${escapeCharacter.value}
  --network chatbot-network ${escapeCharacter.value}
  --gpus=all ${escapeCharacter.value}
  -p ${containerPort}:11434 ${escapeCharacter.value}
  -e model=${aiModel.model} ${escapeCharacter.value}
  -e parameters=${parameters} ${escapeCharacter.value}
  -e port=${containerPort} ${escapeCharacter.value}
  ollama/ollama:latest`

  const pullModelCommand = `docker exec -d ${containerName} ollama pull ${aiModel.model}:${parameters}`

  return [createCommand, pullModelCommand]
}

function canStartContainer(aiModel: IAIModel): boolean {
  const containerStatus = findContainer(aiModel)
  const statuses = ['exited', 'paused']

  return statuses.includes(containerStatus)
}

function startContainer(aiModel: IAIModel) {
  if (!selectedVersions.value[aiModel.model]) {
    return
  }

  containerStore.runContainer({ model: aiModel.model, parameters: selectedVersions.value[aiModel.model]!.parameters })
  snackbarStore.showSnackbarSuccess('Starting container')
}

function startContainerCommand(aiModel: IAIModel): string[] {
  if (!selectedVersions.value[aiModel.model]) {
    return []
  }

  const parameters = selectedVersions.value[aiModel.model]!.parameters
  const containerName = `${aiModel.model}_${parameters}`

  return [`docker start ${containerName}`]
}

function canStopContainer(aiModel: IAIModel): boolean {
  const containerStatus = findContainer(aiModel)
  const statuses = ['running', 'paused', 'restarting', 'pulling_model']

  return statuses.includes(containerStatus)
}

function stopContainer(aiModel: IAIModel) {
  if (!selectedVersions.value[aiModel.model]) {
    return
  }

  containerStore.stopContainer({ model: aiModel.model, parameters: selectedVersions.value[aiModel.model]!.parameters })
  snackbarStore.showSnackbarSuccess('Stopping container')
}

function stopContainerCommand(aiModel: IAIModel): string[] {
  if (!selectedVersions.value[aiModel.model]) {
    return []
  }

  const parameters = selectedVersions.value[aiModel.model]!.parameters
  const containerName = `${aiModel.model}_${parameters}`

  return [`docker stop ${containerName}`]
}

function canRemoveContainer(aiModel: IAIModel): boolean {
  const containerStatus = findContainer(aiModel)
  const statuses = ['running', 'exited', 'paused', 'restarting', 'pulling_model']

  return statuses.includes(containerStatus)
}

function removeContainer(aiModel: IAIModel) {
  if (!selectedVersions.value[aiModel.model]) {
    return
  }

  containerStore.removeContainer({ model: aiModel.model, parameters: selectedVersions.value[aiModel.model]!.parameters })
  snackbarStore.showSnackbarSuccess('Removing container')
}

function removeContainerCommand(aiModel: IAIModel): string[] {
  if (!selectedVersions.value[aiModel.model]) {
    return []
  }

  const parameters = selectedVersions.value[aiModel.model]!.parameters
  const containerName = `${aiModel.model}_${parameters}`

  const stopCommand = stopContainerCommand(aiModel)
  const removeCommand = `docker remove ${containerName}`

  const containerStatus = findContainer(aiModel)
  if (['running', 'pulling_model'].includes(containerStatus))
    return [...stopCommand, removeCommand]

  return [removeCommand]
}

function copyToClipboard(text: string): void {
  navigator.clipboard.writeText(text)
}

function addSearchToQuery(value: string) {
  if (!value) {
    router.push({ query: { ...router.currentRoute.value.query, search: undefined } })

    return
  }

  router.push({ query: { ...router.currentRoute.value.query, search: value } })
}

function addSortToQuery(value: string) {
  router.push({ query: { ...router.currentRoute.value.query, sort: value } })
}

function addFilterToQuery(value: string) {
  router.push({ query: { ...router.currentRoute.value.query, filter: value } })
}

function addWindowsToQuery(value: boolean | null) {
  if (value === null) {
    return
  }

  if (!value)
    router.push({ query: { ...router.currentRoute.value.query, windows: 'false' } })
  else
    router.push({ query: { ...router.currentRoute.value.query, windows: undefined } })
}

function addCanProcessImagesToQuery(value: boolean | null) {
  if (value === null) {
    return
  }

  if (value)
    router.push({ query: { ...router.currentRoute.value.query, canProcessImages: 'true' } })
  else
    router.push({ query: { ...router.currentRoute.value.query, canProcessImages: undefined } })
}

function openPullModelsDialog() {
  if (loading.value)
    return

  isOpenPullModelsDialog.value = true
}
</script>

<template>
  <v-container>
    <div
      style="display: flex; justify-content: space-between; align-items: center;"
      class="mx-2 mb-4"
    >
      <div>
        <v-btn
          class="mr-4"
          @click="() => router.push('/')"
        >
          Go to main page
        </v-btn>

        <v-btn
          @click="() => router.push('/chat')"
        >
          Go to chat page
        </v-btn>
      </div>

      <v-btn @click="openPullModelsDialog">
        {{ loading
          ? "Pulling models. Please wait..."
          : aiModels.length
            ? 'Update models'
            : 'Pull models' }}
      </v-btn>
    </div>

    <v-card :loading="loading">
      <v-card-title>
        <v-row class="mt-0">
          <v-col cols="4">
            <v-text-field
              v-model="search"
              label="Search"
              outlined
              clearable
              prepend-inner-icon="mdi-magnify"
              @update:model-value="addSearchToQuery"
            />
          </v-col>

          <v-col cols="4">
            <v-select
              v-model="sort"
              label="Sort"
              :items="sortItems"
              @update:model-value="addSortToQuery"
            />
          </v-col>

          <v-col cols="4">
            <v-select
              v-model="filter"
              label="Filter"
              :items="filterItems"
              @update:model-value="addFilterToQuery"
            />
          </v-col>

          <v-col cols="4">
            <v-checkbox
              v-model="isWindows"
              color="info"
              label="Windows commands"
              @update:model-value="addWindowsToQuery"
            />
          </v-col>

          <v-col cols="4">
            <v-checkbox
              v-model="canProcessImages"
              color="info"
              label="Can process images"
              @update:model-value="addCanProcessImagesToQuery"
            />
          </v-col>
        </v-row>
      </v-card-title>

      <v-card-text>
        <v-list>
          <v-list-item
            v-for="aiModel in preparedAIModels"
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

              <v-chip
                v-if="aiModel.can_process_image"
                class="mb-1 ml-2"
                density="compact"
                color="success"
                append-icon="mdi-image"
              >
                Image
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

  <PullModelsDialog v-model:is-show="isOpenPullModelsDialog" />
</template>
