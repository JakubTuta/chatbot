<script setup lang="ts">
definePageMeta({ middleware: ['auth'] })

const loading = ref(false)
const isShowDrawer = ref(false)
const temporaryChatTitle = ref('')
const changingChatTitleId = ref('')
const loadingChangeChatTitle = ref(false)
const selectedModel = ref<IContainer | null>(null)
const selectedChatId = ref('')
const forceReset = ref(false)

const authStore = useAuthStore()
const { user } = storeToRefs(authStore)

const chatStore = useChatStore()
const { aiModels, allChats } = storeToRefs(chatStore)

const containerStore = useContainerStore()
const { containers } = storeToRefs(containerStore)

watch(user, async (newValue) => {
  if (!newValue)
    return

  loading.value = true

  if (!aiModels.value.length)
    await chatStore.fetchAIModels()

  if (!containers.value.length)
    await containerStore.getUserContainers()

  loading.value = false
}, { immediate: true })

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

  if (chats.length)
    selectedChatId.value = chats[0].id.toString()
  else
    createNewChat(selectedModel.value.model)
}, { deep: true })

function softReset() {
  temporaryChatTitle.value = ''
  changingChatTitleId.value = ''
  loadingChangeChatTitle.value = false
  forceReset.value = false
}

function changeChat(chat: any) {
  selectedChatId.value = chat.id.toString()
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

async function deleteChat(chat: { id: string }) {
  if (!selectedModel.value)
    return

  await chatStore.deleteChat(selectedModel.value.model, chat.id)

  if (allChats.value[selectedModel.value.model].length)
    selectedChatId.value = allChats.value[selectedModel.value.model][0].id.toString()
  else
    await createNewChat(selectedModel.value.model)
}
</script>

<template>
  <v-row
    class="mx-4 mt-2"
    style="position: absolute; top: 0; left: 0; right: 0; display: flex; justify-content: space-between"
  >
    <v-btn
      v-show="!loading && selectedModel && !isShowDrawer"
      @click="isShowDrawer = !isShowDrawer"
    >
      Show chats
      <v-icon
        size="x-large"
        icon="mdi-chevron-right"
        class="ml-2"
      />
    </v-btn>

    <v-spacer />

    <v-btn
      class="mr-4"
      to="/"
    >
      Main page
    </v-btn>

    <v-btn
      class="mr-4"
      to="/models"
    >
      Models
    </v-btn>

    <v-btn
      v-show="!loading && user"
      @click="authStore.logOut()"
    >
      Logout
    </v-btn>
  </v-row>

  <v-container
    style="max-width: 1000px;"
    class="fill-height"
  >
    <v-navigation-drawer
      v-if="!loading && selectedModel"
      v-model="isShowDrawer"
      width="350"
    >
      <v-list-item class="mb-5 mt-3">
        <v-btn
          block
          @click="isShowDrawer = !isShowDrawer"
        >
          <v-icon
            size="x-large"
            icon="mdi-chevron-left"
            class="mr-2"
          />
          Close chats
        </v-btn>
      </v-list-item>

      <v-list-item
        v-for="chat in allChats[selectedModel.model] || []"
        :key="chat.id"
        :title="isChangingMyTitle(chat)
          ? ''
          : chat.title"
        :ripple="!isChangingMyTitle(chat)"
        :active="selectedChatId === chat.id.toString()"
        @click="changeChat(chat)"
      >
        <v-text-field
          v-if="isChangingMyTitle(chat)"
          v-model="temporaryChatTitle"
          :loading="loadingChangeChatTitle"
          autofocus
          density="comfortable"
          @keydown.enter="acceptChangeChatTitle(chat)"
          @keydown.esc="cancelChangeChatTitle"
          @keydown.space="addSpace"
        />

        <template #append>
          <v-btn
            v-if="!isChangingMyTitle(chat)"
            variant="text"
            icon="mdi-pencil"
            @click="changeChatTitle(chat)"
          />

          <v-btn
            v-if="!isChangingMyTitle(chat)"
            variant="text"
            icon="mdi-delete"
            color="error"
            @click="deleteChat(chat)"
          />

          <v-btn
            v-if="isChangingMyTitle(chat)"
            variant="text"
            icon="mdi-close"
            color="error"
            class="mb-6"
            @click="cancelChangeChatTitle()"
          />
        </template>
      </v-list-item>

      <v-list-item class="mt-5">
        <v-btn
          block
          @click="createNewChat(selectedModel.model)"
        >
          Create new chat

          <v-icon
            size="x-large"
            icon="mdi-plus"
            color="success"
            class="ml-2"
          />
        </v-btn>
      </v-list-item>
    </v-navigation-drawer>

    <v-card v-if="loading">
      <v-skeleton-loader
        class="mx-auto"
        height="250"
        width="100%"
      />
    </v-card>

    <ChatCard
      v-else
      v-model:selected-model="selectedModel"
      :reset="forceReset"
      :selected-chat-id="selectedChatId"
      @soft-reset="softReset"
    />
  </v-container>
</template>
