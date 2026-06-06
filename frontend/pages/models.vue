<script setup lang="ts">
import type { IAIModel } from '~/models/aiModel'
import { useThemeToggle } from '~/composables/useTheme'

const router = useRouter()
const { isDark, toggleTheme } = useThemeToggle()

const containerStore = useContainerStore()
const { containers, loadingOperation, pullProgress, scrapeProgress } = storeToRefs(containerStore)

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
  if (query.search)
    search.value = query.search as string
  if (query.sort)
    sort.value = query.sort as string
  if (query.filter)
    filter.value = query.filter as string
  if (query.windows)
    isWindows.value = query.windows === 'true'
  if (query.canProcessImages)
    canProcessImages.value = query.canProcessImages === 'true'

  // Instant paint before socket connects
  await containerStore.getUserContainers()
  containerStore.connectSocket()

  await chatStore.fetchAIModels()
})

onUnmounted(() => {
  containerStore.disconnectSocket()
})

// When scrape finishes, refresh model list
watch(
  () => scrapeProgress.value.running,
  (running, wasRunning) => {
    if (wasRunning && !running && !scrapeProgress.value.error) {
      chatStore.fetchAIModels()
      snackbarStore.showSnackbarSuccess('Models updated successfully!')
    }
  },
)

// ─── Computed: filtered + sorted model list ───────────────────────────────────

const preparedAIModels = computed(() => {
  const searchFn = (model: IAIModel) => !search.value || model.name.toLowerCase().includes(search.value.toLowerCase())

  const sortFn = (a: IAIModel, b: IAIModel) => {
    if (sort.value === 'popularityDecreasing')
      return b.popularity - a.popularity
    if (sort.value === 'popularityIncreasing')
      return a.popularity - b.popularity
    if (sort.value === 'nameAlphabetically')
      return a.name.localeCompare(b.name)
    if (sort.value === 'nameReverseAlphabetically')
      return b.name.localeCompare(a.name)

    return 0
  }

  const filterFn = (containerStatus: string) => {
    if (filter.value === 'all')
      return true
    if (filter.value === 'allMyModels')
      return containerStatus !== 'not_found'
    if (filter.value === 'runningContainers')
      return containerStatus === 'running'
    if (filter.value === 'exitedContainers')
      return containerStatus === 'exited'
    if (filter.value === 'pausedContainers')
      return containerStatus === 'paused'
    if (filter.value === 'restartingContainers')
      return containerStatus === 'restarting'
    if (filter.value === 'pullingModelContainers')
      return containerStatus === 'pulling_model'
    if (filter.value === 'notFoundContainers')
      return containerStatus === 'not_found'

    return true
  }

  const canProcessImageFn = (model: IAIModel) => (canProcessImages.value
    ? model.can_process_image
    : true)

  const withVersions = aiModels.value
    .filter(searchFn)
    .filter(canProcessImageFn)
    .sort(sortFn)
    .map((model) => {
      const filteredVersions = model.versions.filter((version) => {
        const containerName = `${model.model}_${version.parameters}`
        const containerStatus = getContainerStatusByName(containerName)

        return filterFn(containerStatus)
      })

      return { ...model, versions: filteredVersions }
    })
    .filter(model => model.versions.length > 0)

  // Installed models (any container exists) float to the top
  const installed = withVersions.filter(m => getInstalledVersionCount(m) > 0)
  const rest = withVersions.filter(m => getInstalledVersionCount(m) === 0)

  return [...installed, ...rest]
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

// ─── Container helpers ────────────────────────────────────────────────────────

function getContainerName(model: IAIModel): string | null {
  if (!selectedVersions.value[model.model])
    return null

  return `${model.model}_${selectedVersions.value[model.model]!.parameters}`
}

function getContainerStatusByName(containerName: string): string {
  return containers.value.find(c => c.name === containerName)?.status ?? 'not_found'
}

function getContainerStatus(model: IAIModel): string {
  const name = getContainerName(model)
  if (!name)
    return 'not_found'

  return getContainerStatusByName(name)
}

function getModelPullProgress(model: IAIModel) {
  const name = getContainerName(model)
  if (!name)
    return null

  return pullProgress.value[name] ?? null
}

function isOperationLoading(model: IAIModel): boolean {
  const name = getContainerName(model)
  if (!name)
    return false
  const opKey = loadingOperation.value ?? ''

  return opKey.includes(model.model)
}

function getInstalledVersionCount(model: IAIModel): number {
  return model.versions.filter(v => getContainerStatusByName(`${model.model}_${v.parameters}`) !== 'not_found',
  ).length
}

// ─── Status display ────────────────────────────────────────────────────────────

const statusConfig: Record<string, { color: string, icon: string, label: string }> = {
  running: { color: 'success', icon: 'mdi-play-circle', label: 'Running' },
  exited: { color: 'default', icon: 'mdi-stop-circle-outline', label: 'Exited' },
  paused: { color: 'warning', icon: 'mdi-pause-circle-outline', label: 'Paused' },
  restarting: { color: 'warning', icon: 'mdi-restart', label: 'Restarting' },
  pulling_model: { color: 'info', icon: 'mdi-download', label: 'Pulling model' },
  not_found: { color: 'default', icon: 'mdi-circle-outline', label: 'Not found' },
}

function statusChipProps(status: string) {
  return statusConfig[status] ?? statusConfig.not_found
}

// ─── Primary action logic ──────────────────────────────────────────────────────

interface ActionConfig {
  label: string
  color: string
  disabled: boolean
  loading: boolean
  handler: () => void
}

function getPrimaryAction(model: IAIModel): ActionConfig {
  if (!selectedVersions.value[model.model]) {
    return { label: 'Select a version first', color: 'default', disabled: true, loading: false, handler: () => {} }
  }

  const containerStatus = getContainerStatus(model)
  const progress = getModelPullProgress(model)
  const operationLoading = isOperationLoading(model)

  if (progress) {
    return { label: 'Downloading…', color: 'primary', disabled: true, loading: true, handler: () => {} }
  }

  if (operationLoading || containerStatus === 'restarting') {
    return { label: 'Please wait…', color: 'default', disabled: true, loading: true, handler: () => {} }
  }

  if (containerStatus === 'not_found') {
    return {
      label: 'Create container',
      color: 'success',
      disabled: false,
      loading: false,
      handler: () => createContainer(model),
    }
  }

  if (containerStatus === 'exited' || containerStatus === 'paused') {
    return {
      label: 'Start container',
      color: 'success',
      disabled: false,
      loading: false,
      handler: () => startContainer(model),
    }
  }

  if (containerStatus === 'running') {
    return {
      label: 'Stop container',
      color: 'warning',
      disabled: false,
      loading: false,
      handler: () => stopContainer(model),
    }
  }

  if (containerStatus === 'pulling_model') {
    return { label: 'Pulling model…', color: 'info', disabled: true, loading: true, handler: () => {} }
  }

  return { label: 'N/A', color: 'default', disabled: true, loading: false, handler: () => {} }
}

function canRemove(model: IAIModel): boolean {
  const s = getContainerStatus(model)

  return ['running', 'exited', 'paused', 'restarting', 'pulling_model'].includes(s)
}

// ─── Actions ──────────────────────────────────────────────────────────────────

function createContainer(model: IAIModel) {
  if (!selectedVersions.value[model.model])
    return
  containerStore.runContainer({ model: model.model, parameters: selectedVersions.value[model.model]!.parameters })
  snackbarStore.showSnackbarInfo('Container creation started — progress shown on card')
}

function startContainer(model: IAIModel) {
  if (!selectedVersions.value[model.model])
    return
  containerStore.runContainer({ model: model.model, parameters: selectedVersions.value[model.model]!.parameters })
  snackbarStore.showSnackbarSuccess('Starting container')
}

function stopContainer(model: IAIModel) {
  if (!selectedVersions.value[model.model])
    return
  containerStore.stopContainer({ model: model.model, parameters: selectedVersions.value[model.model]!.parameters })
  snackbarStore.showSnackbarSuccess('Stopping container')
}

function removeContainer(model: IAIModel) {
  if (!selectedVersions.value[model.model])
    return
  containerStore.removeContainer({ model: model.model, parameters: selectedVersions.value[model.model]!.parameters })
  snackbarStore.showSnackbarSuccess('Removing container')
}

// ─── CLI commands ─────────────────────────────────────────────────────────────

function createContainerCommand(model: IAIModel): string[] {
  if (!selectedVersions.value[model.model])
    return []
  const parameters = selectedVersions.value[model.model]!.parameters
  const containerName = `${model.model}_${parameters}`
  const containerPort = 11434 + model.index

  const createCommand = `docker run -d ${escapeCharacter.value}
  --name ${containerName} ${escapeCharacter.value}
  --network chatbot-network ${escapeCharacter.value}
  --gpus=all ${escapeCharacter.value}
  -p ${containerPort}:11434 ${escapeCharacter.value}
  -e model=${model.model} ${escapeCharacter.value}
  -e parameters=${parameters} ${escapeCharacter.value}
  -e port=${containerPort} ${escapeCharacter.value}
  ollama/ollama:latest`

  const pullModelCommand = `docker exec -d ${containerName} ollama pull ${model.model}:${parameters}`

  return [createCommand, pullModelCommand]
}

function startContainerCommand(model: IAIModel): string[] {
  if (!selectedVersions.value[model.model])
    return []
  const parameters = selectedVersions.value[model.model]!.parameters
  const containerName = `${model.model}_${parameters}`

  return [`docker start ${containerName}`]
}

function stopContainerCommand(model: IAIModel): string[] {
  if (!selectedVersions.value[model.model])
    return []
  const parameters = selectedVersions.value[model.model]!.parameters
  const containerName = `${model.model}_${parameters}`

  return [`docker stop ${containerName}`]
}

function removeContainerCommand(model: IAIModel): string[] {
  if (!selectedVersions.value[model.model])
    return []
  const containerStatus = getContainerStatus(model)
  const stopCmds = ['running', 'pulling_model'].includes(containerStatus)
    ? stopContainerCommand(model)
    : []
  const containerName = `${model.model}_${selectedVersions.value[model.model]!.parameters}`

  return [...stopCmds, `docker rm ${containerName}`]
}

function allCliCommands(model: IAIModel): string[] {
  if (!selectedVersions.value[model.model])
    return []
  const containerStatus = getContainerStatus(model)
  if (containerStatus === 'not_found')
    return createContainerCommand(model)
  const cmds: string[] = []
  if (['exited', 'paused'].includes(containerStatus))
    cmds.push(...startContainerCommand(model))
  if (['running', 'paused', 'restarting', 'pulling_model'].includes(containerStatus))
    cmds.push(...stopContainerCommand(model))
  cmds.push(...removeContainerCommand(model))

  return cmds
}

function copyToClipboard(text: string): void {
  navigator.clipboard.writeText(text)
}

// ─── Formatting helpers ───────────────────────────────────────────────────────

function formatNumber(num: number): string {
  if (num >= 1_000_000)
    return `${(num / 1_000_000).toFixed(1)}M`
  if (num >= 1_000)
    return `${(num / 1_000).toFixed(1)}K`

  return num.toString()
}

function chipColor(value: number): string {
  if (value >= 1_000_000)
    return 'blue'
  if (value >= 1_000)
    return 'green'

  return 'gray'
}

// ─── Query param sync ─────────────────────────────────────────────────────────

function addSearchToQuery(value: string) {
  router.push({ query: { ...router.currentRoute.value.query, search: value || undefined } })
}

function addSortToQuery(value: string) {
  router.push({ query: { ...router.currentRoute.value.query, sort: value } })
}

function addFilterToQuery(value: string) {
  router.push({ query: { ...router.currentRoute.value.query, filter: value } })
}

function addWindowsToQuery(value: boolean | null) {
  if (value === null)
    return
  router.push({ query: { ...router.currentRoute.value.query, windows: value
    ? undefined
    : 'false' } })
}

function addCanProcessImagesToQuery(value: boolean | null) {
  if (value === null)
    return
  router.push({ query: { ...router.currentRoute.value.query, canProcessImages: value
    ? 'true'
    : undefined } })
}

function openPullModelsDialog() {
  if (loading.value)
    return
  isOpenPullModelsDialog.value = true
}
</script>

<template>
  <v-container>
    <SystemStatusBanner />

    <!-- ── Header ── -->
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

        <v-btn @click="() => router.push('/chat')">
          Go to chat page
        </v-btn>
      </div>

      <div class="d-flex align-center gap-2">
        <v-btn
          icon
          variant="text"
          :title="isDark
            ? 'Switch to light mode'
            : 'Switch to dark mode'"
          @click="toggleTheme"
        >
          <v-icon>
            {{ isDark
              ? 'mdi-weather-sunny'
              : 'mdi-weather-night' }}
          </v-icon>
        </v-btn>

        <v-btn @click="openPullModelsDialog">
          {{ scrapeProgress.running
            ? `Scraping… ${scrapeProgress.total
              ? `${scrapeProgress.completed}/${scrapeProgress.total}`
              : ''}`
            : loading
              ? 'Loading…'
              : aiModels.length
                ? 'Update models'
                : 'Pull models' }}
        </v-btn>
      </div>
    </div>

    <!-- ── Filters ── -->
    <v-card
      class="mb-4"
      :loading="loading"
    >
      <v-card-text>
        <v-row dense>
          <v-col
            cols="12"
            sm="4"
          >
            <v-text-field
              v-model="search"
              label="Search"
              variant="outlined"
              density="compact"

              hide-details
              clearable
              prepend-inner-icon="mdi-magnify"
              @update:model-value="addSearchToQuery"
            />
          </v-col>

          <v-col
            cols="12"
            sm="4"
          >
            <v-select
              v-model="sort"
              label="Sort"
              :items="sortItems"
              variant="outlined"
              density="compact"
              hide-details
              @update:model-value="addSortToQuery"
            />
          </v-col>

          <v-col
            cols="12"
            sm="4"
          >
            <v-select
              v-model="filter"
              label="Filter"
              :items="filterItems"
              variant="outlined"
              density="compact"
              hide-details
              @update:model-value="addFilterToQuery"
            />
          </v-col>

          <v-col
            cols="12"
            sm="6"
            class="d-flex align-center gap-4"
          >
            <v-checkbox
              v-model="isWindows"
              color="info"
              label="Windows commands"
              density="compact"
              hide-details
              @update:model-value="addWindowsToQuery"
            />

            <v-checkbox
              v-model="canProcessImages"
              color="info"
              label="Can process images"
              density="compact"
              hide-details
              @update:model-value="addCanProcessImagesToQuery"
            />
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <!-- ── Empty state ── -->
    <div
      v-if="!loading && !preparedAIModels.length"
      class="py-12 text-center"
    >
      <v-icon
        size="64"
        icon="mdi-robot-off-outline"
        class="d-block text-medium-emphasis mb-4"
      />

      <div class="text-h5 mb-2">
        No AI models found
      </div>

      <div class="text-body-1 text-medium-emphasis mb-6">
        Click <strong>Pull models</strong>
        to fetch the list from
        <a
          href="https://ollama.com/library"
          target="_blank"
          rel="noopener"
          class="text-primary"
        >ollama.com</a>
        .
        Then select a version on a model card and click <strong>Create container</strong> to download and run it.
      </div>

      <v-btn
        color="primary"
        @click="openPullModelsDialog"
      >
        Pull models
      </v-btn>
    </div>

    <!-- ── Model cards ── -->
    <v-row>
      <v-col
        v-for="model in preparedAIModels"
        :key="model.model"
        cols="12"
        sm="6"
        lg="4"
      >
        <v-card
          variant="outlined"
          class="d-flex flex-column h-100"
          :style="getInstalledVersionCount(model)
            ? 'border-color: rgb(var(--v-theme-primary)); border-width: 2px'
            : ''"
        >
          <!-- Card header -->
          <v-card-title
            class="flex-wrap pb-1"
            style="gap: 4px"
          >
            <span>{{ model.name }}</span>

            <v-chip
              class="ml-2"
              density="compact"
              :color="chipColor(model.popularity)"
              append-icon="mdi-download"
            >
              {{ formatNumber(model.popularity) }}
            </v-chip>

            <v-chip
              v-if="model.can_process_image"
              class="ml-1"
              density="compact"
              color="success"
              append-icon="mdi-image"
            >
              Vision
            </v-chip>

            <v-chip
              v-if="getInstalledVersionCount(model)"
              class="ml-1"
              density="compact"
              color="primary"
              prepend-icon="mdi-check-circle"
            >
              {{ getInstalledVersionCount(model) }} installed
            </v-chip>
          </v-card-title>

          <v-card-subtitle class="text-wrap">
            {{ model.description }}
          </v-card-subtitle>

          <v-card-text class="flex-grow-1">
            <!-- Version selector -->
            <v-select
              v-model="selectedVersions[model.model]"
              :items="model.versions"
              clearable
              label="Version"
              variant="outlined"
              density="compact"
              return-object
              :item-title="(item: any) => `${item.parameters} parameters — ${item.size}`"
            />

            <!-- Status row -->
            <div
              v-if="selectedVersions[model.model]"
              class="d-flex align-center mb-3 gap-2"
            >
              <v-chip
                density="compact"
                :color="statusChipProps(getContainerStatus(model)).color"
                :prepend-icon="statusChipProps(getContainerStatus(model)).icon"
              >
                {{ statusChipProps(getContainerStatus(model)).label }}
              </v-chip>

              <span
                v-if="selectedVersions[model.model]"
                class="text-caption text-medium-emphasis"
              >
                {{ selectedVersions[model.model]!.parameters }} · {{ selectedVersions[model.model]!.size }}
              </span>
            </div>

            <!-- Progress bar -->
            <template v-if="getModelPullProgress(model)">
              <div class="d-flex justify-space-between align-center mb-1">
                <span class="text-caption text-medium-emphasis">
                  {{ getModelPullProgress(model)!.phase === 'image_pull_progress'
                    ? 'Downloading base image'
                    : 'Pulling model' }}
                </span>

                <span class="text-caption font-weight-medium">
                  {{ getModelPullProgress(model)!.percent }}%
                </span>
              </div>

              <v-progress-linear
                :model-value="getModelPullProgress(model)!.percent"
                color="primary"
                rounded
                height="6"
                class="mb-1"
              />

              <div class="text-caption text-disabled mb-3">
                {{ getModelPullProgress(model)!.detail }}
              </div>
            </template>

            <!-- Action buttons -->
            <div
              v-if="selectedVersions[model.model]"
              class="d-flex align-center gap-2"
            >
              <v-btn
                :color="getPrimaryAction(model).color"
                :disabled="getPrimaryAction(model).disabled"
                :loading="getPrimaryAction(model).loading"
                size="small"
                style="min-width: 150px"
                @click="getPrimaryAction(model).handler()"
              >
                <template v-if="!getPrimaryAction(model).loading">
                  {{ getPrimaryAction(model).label }}
                </template>
              </v-btn>

              <v-btn
                v-if="canRemove(model)"
                color="error"
                variant="outlined"
                size="small"
                :disabled="isOperationLoading(model)"
                @click="removeContainer(model)"
              >
                Remove
              </v-btn>
            </div>

            <div
              v-else
              class="text-caption text-medium-emphasis"
            >
              Select a version to manage this model.
            </div>

            <!-- Advanced CLI panel -->
            <v-expansion-panels
              v-if="selectedVersions[model.model] && allCliCommands(model).length"
              class="mt-3"
              variant="accordion"
            >
              <v-expansion-panel>
                <v-expansion-panel-title class="text-caption">
                  Advanced: run manually
                </v-expansion-panel-title>

                <v-expansion-panel-text>
                  <v-textarea
                    v-for="(cmd, idx) in allCliCommands(model)"
                    :key="idx"
                    :model-value="cmd"
                    append-inner-icon="mdi-content-copy"
                    auto-grow
                    readonly
                    no-resize
                    rows="1"
                    density="compact"
                    class="mb-2"
                    @click:append-inner="copyToClipboard(cmd)"
                  />
                </v-expansion-panel-text>
              </v-expansion-panel>
            </v-expansion-panels>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>

  <PullModelsDialog v-model:is-show="isOpenPullModelsDialog" />
</template>
