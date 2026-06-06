<script setup lang="ts">
import { useDisplay } from 'vuetify'
import { useThemeToggle } from '~/composables/useTheme'

const { isDark, toggleTheme } = useThemeToggle()
const { mobile } = useDisplay()

const loading = ref(false)
const isShowDrawer = ref(!mobile.value)
const temporaryChatTitle = ref('')
const changingChatTitleId = ref('')
const loadingChangeChatTitle = ref(false)
const selectedModel = ref<IContainer | null>(null)
const selectedChatId = ref('')
const forceReset = ref(false)

const confirmDeleteDialog = ref(false)
const chatToDelete = ref<{ id: string } | null>(null)

const chatStore = useChatStore()
const { aiModels, allChats } = storeToRefs(chatStore)

const containerStore = useContainerStore()
const { containers } = storeToRefs(containerStore)

onMounted(async () => {
  loading.value = true

  if (!aiModels.value.length)
    await chatStore.fetchAIModels()

  if (!containers.value.length)
    await containerStore.getUserContainers()

  containerStore.startPolling()

  loading.value = false
})

onUnmounted(() => {
  containerStore.stopPolling()
})

watch(selectedChatId, async (newChatId, oldChatId) => {
  if (!newChatId || !selectedModel.value || newChatId === oldChatId)
    return

  loading.value = true
  forceReset.value = true

  await chatStore.fetchChatHistory(selectedModel.value.model, newChatId)

  loading.value = false
}, { immediate: true })

watch(allChats, (newValue) => {
  if (!selectedModel.value || !newValue[selectedModel.value.model])
    return

  const chats = newValue[selectedModel.value.model]
  const currentValid = chats.some(c => c.id.toString() === selectedChatId.value)

  if (!currentValid) {
    if (chats.length)
      selectedChatId.value = chats[0].id.toString()
    else
      createNewChat(selectedModel.value.model)
  }
}, { deep: true })

function softReset() {
  temporaryChatTitle.value = ''
  changingChatTitleId.value = ''
  loadingChangeChatTitle.value = false
  forceReset.value = false
}

function changeChat(chat: any) {
  selectedChatId.value = chat.id.toString()
  if (mobile.value)
    isShowDrawer.value = false
}

function changeChatTitle(chat: { id: string, title: string }) {
  temporaryChatTitle.value = chat.title
  changingChatTitleId.value = chat.id
}

function isChangingMyTitle(chat: { id: string }) {
  if (!changingChatTitleId.value)
    return false

  return changingChatTitleId.value === chat.id
}

async function acceptChangeChatTitle(chat: { id: string, title: string }) {
  if (!chat.title || !selectedModel.value)
    return

  loadingChangeChatTitle.value = true

  const model = selectedModel.value.model
  await chatStore.changeChatTitle(model, chat, temporaryChatTitle.value)

  loadingChangeChatTitle.value = false
  changingChatTitleId.value = ''
  temporaryChatTitle.value = ''
}

function cancelChangeChatTitle() {
  changingChatTitleId.value = ''
  temporaryChatTitle.value = ''
}

function addSpace() {
  if (!changingChatTitleId.value)
    return

  temporaryChatTitle.value += ' '
}

async function createNewChat(model: string) {
  const newChatId = await chatStore.createChat(model)

  if (newChatId !== null)
    selectedChatId.value = newChatId.toString()
}

function deleteChat(chat: { id: string }) {
  chatToDelete.value = chat
  confirmDeleteDialog.value = true
}

async function confirmDeleteChat() {
  confirmDeleteDialog.value = false

  if (!selectedModel.value || !chatToDelete.value)
    return

  await chatStore.deleteChat(selectedModel.value.model, chatToDelete.value.id)
  chatToDelete.value = null

  if (allChats.value[selectedModel.value.model]?.length)
    selectedChatId.value = allChats.value[selectedModel.value.model][0].id.toString()
  else
    await createNewChat(selectedModel.value.model)
}

function cancelDeleteChat() {
  confirmDeleteDialog.value = false
  chatToDelete.value = null
}
</script>

<template>
  <v-app-bar
    flat
    elevation="0"
    border="b"
    class="frosted-bar"
  >
    <v-app-bar-nav-icon
      v-if="selectedModel"
      @click="isShowDrawer = !isShowDrawer"
    />

    <v-app-bar-title>
      <span class="app-title">OllamaChat</span>
    </v-app-bar-title>

    <template #append>
      <v-btn
        variant="text"
        rounded="xl"
        to="/"
      >
        Home
      </v-btn>

      <v-btn
        variant="text"
        rounded="xl"
        to="/models"
        class="mr-1"
      >
        Models
      </v-btn>

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
    </template>
  </v-app-bar>

  <v-navigation-drawer
    v-if="selectedModel"
    v-model="isShowDrawer"
    :temporary="mobile"
    width="280"
    class="chat-drawer"
  >
    <div class="align-center d-flex justify-space-between px-4 pb-2 pt-4">
      <span class="text-medium-emphasis font-weight-medium text-caption drawer-label tracking-widest">
        CONVERSATIONS
      </span>

      <v-btn
        icon="mdi-plus"
        variant="text"
        size="small"
        title="New chat"
        class="new-chat-btn"
        @click="createNewChat(selectedModel!.model)"
      />
    </div>

    <v-divider />

    <v-list
      density="compact"
      nav
      class="px-2 pt-2"
    >
      <v-list-item
        v-for="chat in allChats[selectedModel.model] || []"
        :key="chat.id"
        :ripple="!isChangingMyTitle(chat)"
        :active="selectedChatId === chat.id.toString()"
        active-color="primary"
        rounded="lg"
        min-height="44"
        class="chat-list-item"
        :class="{'chat-list-item--active': selectedChatId === chat.id.toString()}"
        @click="changeChat(chat)"
      >
        <template #title>
          <v-text-field
            v-if="isChangingMyTitle(chat)"
            v-model="temporaryChatTitle"
            :loading="loadingChangeChatTitle"
            density="compact"
            variant="plain"
            hide-details
            autofocus
            @keydown.enter="acceptChangeChatTitle(chat)"
            @keydown.esc="cancelChangeChatTitle"
            @keydown.space.prevent="addSpace"
          />

          <span
            v-else
            class="d-block text-truncate"
            style="max-width: 152px; font-size: 0.875rem"
          >
            {{ chat.title }}
          </span>
        </template>

        <template #append>
          <template v-if="!isChangingMyTitle(chat)">
            <v-btn
              icon="mdi-pencil"
              variant="text"
              size="x-small"
              class="drawer-action-btn"
              @click.stop="changeChatTitle(chat)"
            />

            <v-btn
              icon="mdi-delete"
              variant="text"
              size="x-small"
              color="error"
              class="drawer-action-btn"
              @click.stop="deleteChat(chat)"
            />
          </template>

          <v-btn
            v-else
            icon="mdi-close"
            variant="text"
            size="x-small"
            color="error"
            @click.stop="cancelChangeChatTitle()"
          />
        </template>
      </v-list-item>
    </v-list>
  </v-navigation-drawer>

  <ConfirmDialog
    v-model="confirmDeleteDialog"
    title="Delete chat"
    message="Are you sure you want to delete this chat? This action cannot be undone."
    confirm-label="Delete"
    confirm-color="error"
    @confirm="confirmDeleteChat"
    @cancel="cancelDeleteChat"
  />

  <div class="chat-page-content">
    <div
      v-if="loading"
      class="d-flex align-center justify-center"
      style="height: 100%"
    >
      <v-progress-circular indeterminate />
    </div>

    <template v-else>
      <SystemStatusBanner class="chat-page-banner" />

      <ChatCard
        v-model:selected-model="selectedModel"
        :reset="forceReset"
        :selected-chat-id="selectedChatId"
        @soft-reset="softReset"
      />
    </template>
  </div>
</template>

<style scoped>
/* Frosted app bar */
.frosted-bar {
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  background: rgba(var(--v-theme-surface), 0.82) !important;
}

/* Gradient app title */
.app-title {
  font-size: 1.125rem;
  font-weight: 700;
  background: linear-gradient(135deg, #6366F1, #818CF8);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

/* Drawer */
.chat-drawer {
  background: rgb(var(--v-theme-surface)) !important;
}

.drawer-label {
  letter-spacing: 0.08em;
}

.new-chat-btn {
  color: #6366F1 !important;
  transition: transform 0.5s ease;
}

.new-chat-btn:hover {
  transform: rotate(90deg);
}

/* Chat list items */
.chat-list-item {
  transition: background-color 0.15s ease;
}

.chat-list-item--active {
  border-left: 2px solid #6366F1;
}

/* Hide action buttons until hover */
.drawer-action-btn {
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.15s ease;
}

.chat-list-item:hover .drawer-action-btn {
  opacity: 1;
  pointer-events: auto;
}

/* Always show on touch */
@media (hover: none) {
  .drawer-action-btn {
    opacity: 1;
    pointer-events: auto;
  }
}

/* Chat page layout */
.chat-page-content {
  display: flex;
  flex-direction: column;
  height: calc(100dvh - 64px);
  padding: 12px 24px 16px;
  overflow: hidden;
}

.chat-page-banner {
  flex-shrink: 0;
  margin-bottom: 8px;
}
</style>
