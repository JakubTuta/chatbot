<script setup lang="ts">
import { useDisplay } from 'vuetify';

definePageMeta({ middleware: ['auth'] })

export interface ContainerModel {
  name: string
  value: string
  model: string
  status: string
  parameters: string
  canProcessImages: boolean
}

const loading = ref(false)
const selectedModel = ref<ContainerModel | null>(null)
const message = ref('')
const selectedChatId = ref('')
const isShowDrawer = ref(false)
const temporaryChatTitle = ref('')
const changingChatTitleId = ref('')
const loadingChangeChatTitle = ref(false)
const image = ref('')

const userMessageColor = '#168AFF'
const botMessageColor = '#9F33FF'

const { height, mobile } = useDisplay()
const router = useRouter()

const authStore = useAuthStore()
const { isAuthorized } = storeToRefs(authStore)

const chatStore = useChatStore()
const { aiModels, chatHistoryPerModel, allChats, sendingMessage } = storeToRefs(chatStore)

const containerStore = useContainerStore()
const { containers } = storeToRefs(containerStore)

const userPulledModels = computed(() => {
  if (!containers.value.length || !aiModels.value.length)
    return []

  return containers.value.map((container) => {
    if (container.status === 'pulling_model')
      return null

    const containerModel = container.environment.model
    const foundAIModel = aiModels.value.find(model => model.model === containerModel)

    if (!foundAIModel)
      return null

    return {
      name: foundAIModel.name,
      value: `${foundAIModel.model} - ${container.environment.parameters}`,
      model: containerModel,
      status: container.status,
      parameters: container.environment.parameters,
      canProcessImages: foundAIModel.can_process_image,
    } as ContainerModel
  })
    .filter(e => e !== null)
    .sort((a, b) => a.value.localeCompare(b.value))
})

watch(userPulledModels, (newValue) => {
  if (newValue.length)
    selectedModel.value = newValue[0]
})

watch(isAuthorized, async (newValue) => {
  if (!newValue)
    return

  loading.value = true

  if (!aiModels.value.length)
    await chatStore.fetchAIModels()

  if (!containers.value.length)
    await containerStore.getUserContainers()

  loading.value = false
}, { immediate: true })

watch(selectedModel, async (newModel, oldModel) => {
  if (!newModel
    || (newModel.model === (oldModel?.model || '')
      && newModel.parameters === (oldModel?.parameters || ''))) {
    return
  }

  loading.value = true
  softReset()

  containerStore.runContainer(newModel)

  const chats = allChats.value[newModel.model] || []

  if (!chats.length) {
    await chatStore.fetchAllChats(newModel.model)

    const updatedChats = allChats.value[newModel.model] || []

    if (updatedChats.length)
      selectedChatId.value = updatedChats[0].id
    else
      await createNewChat(newModel.model)
  }

  const newQueryParams = {
    model: newModel.model,
    parameters: newModel.parameters,
    chatId: selectedChatId.value,
  }
  router.push({ query: newQueryParams })

  loading.value = false
}, { immediate: true })

watch(selectedChatId, async (newChatId, oldChatId) => {
  if (!newChatId || !selectedModel.value || newChatId === oldChatId)
    return

  loading.value = true
  softReset()

  await chatStore.fetchChatHistory(selectedModel.value.model, newChatId)

  router.push({ query: { ...router.currentRoute.value.query, chatId: newChatId } })

  loading.value = false
}, { immediate: true })

function softReset() {
  message.value = ''
  temporaryChatTitle.value = ''
  changingChatTitleId.value = ''
  loadingChangeChatTitle.value = false
  image.value = ''
}

function sendQuestion() {
  if (!selectedModel.value || !message.value || !selectedChatId.value)
    return

  const model = selectedModel.value.model
  const modelParameters = selectedModel.value.parameters

  chatStore.askBot(model, modelParameters, selectedChatId.value, message.value, image.value)

  message.value = ''
  image.value = ''
}

function changeChat(chat: { id: string }) {
  selectedChatId.value = chat.id
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
    selectedChatId.value = newChatId
}

function goToModels() {
  router.push('/models')
}

function goToMainPage() {
  router.push('/')
}

function toBase64(file: Blob) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.readAsDataURL(file)
    reader.onload = () => resolve(reader.result)
    reader.onerror = error => reject(error)
  })
}

async function handleImageUpload(event: any) {
  if (!event.target?.files.length)
    return

  const file = event.target.files[0]

  const fileInBase64 = await toBase64(file) as string
  image.value = fileInBase64
}

function clearImage() {
  image.value = ''
}

async function deleteChat(chat: { id: string }) {
  if (!selectedModel.value)
    return

  await chatStore.deleteChat(selectedModel.value.model, chat.id)

  if (allChats.value[selectedModel.value.model].length)
    selectedChatId.value = allChats.value[selectedModel.value.model][0].id
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
      @click="goToMainPage"
    >
      Main page
    </v-btn>

    <v-btn
      class="mr-4"
      @click="goToModels"
    >
      Models
    </v-btn>

    <v-btn
      v-show="!loading && isAuthorized"
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
        :active="selectedChatId === chat.id"
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

    <v-card v-else>
      <v-card-text>
        <v-row>
          <v-col
            cols="12"
            sm="5"
            md="4"
          >
            <v-select
              v-model="selectedModel"
              label="AI Model"
              :items="userPulledModels"
              :item-title="item => `${item.name} - ${item.parameters}`"
              return-object
            >
              <template #prepend-item>
                <v-list-item
                  @click="goToModels"
                >
                  Add more models

                  <v-icon
                    icon="mdi-arrow-right"
                    class="ml-2"
                  />
                </v-list-item>

                <v-divider class="my-2" />
              </template>

              <template #no-data />
            </v-select>
          </v-col>
        </v-row>

        <v-card
          variant="outlined"
          width="100%"
          height="100%"
        >
          <v-card-text>
            <v-list
              :max-height="mobile
                ? `${height - 360}px`
                : `${height - 450}px`"
            >
              <div
                v-for="(chatMessage, index) in chatHistoryPerModel[selectedModel?.model || ''] || []"
                :key="index"
                :style="chatMessage.role === 'user'
                  ? 'justify-content: flex-end'
                  : 'justify-content: flex-start'"
                style="display: flex"
                :class="index === 0
                  ? ''
                  : 'mt-4'"
              >
                <v-list-item
                  rounded="shaped"
                  :style="chatMessage.role === 'user'
                    ? `background-color: ${userMessageColor}`
                    : `background-color: ${botMessageColor}`"
                  :max-width="mobile
                    ? '90%'
                    : '70%'"
                  :class="chatMessage.role === 'user'
                    ? 'text-align-end'
                    : 'text-align-start'"
                  class="px-4 py-2"
                >
                  <span class="text-subtitle-2">
                    {{ chatMessage.content }}
                  </span>

                  <p
                    v-if="chatMessage.image"
                    align="end"
                    class="mt-2"
                  >
                    <img
                      :src="chatMessage.image"
                      alt="Uploaded image"
                      style="max-width: 100%; max-height: 100px"
                    >
                  </p>
                </v-list-item>
              </div>
            </v-list>

            <v-spacer class="mt-4" />

            <span
              v-if="sendingMessage"
              class="text-gray"
            >
              Bot is thinking...
            </span>

            <v-row
              v-if="image"
              justify="end"
              class="ma-0"
            >
              <v-badge
                icon="mdi-close"
                color="error"
                @click="clearImage"
              >
                <img
                  :src="image"
                  alt="Uploaded image"
                  style="max-width: 100%; max-height: 100px"
                >
              </v-badge>
            </v-row>
          </v-card-text>
        </v-card>

        <v-row class="mx-2 mt-4">
          <v-text-field
            v-model="message"
            label="Message"
            @keydown.enter="sendQuestion"
          />

          <v-btn
            v-if="selectedModel?.canProcessImages"
            variant="flat"
            class="ml-4 mt-1"
            icon
            @click="$refs.fileInput.click()"
          >
            <v-icon
              size="x-large"
              icon="mdi-file-upload-outline"
            />

            <input
              ref="fileInput"
              type="file"
              accept="image/*"
              style="display: none"
              @change="handleImageUpload"
            >
          </v-btn>

          <v-btn
            variant="flat"
            class="ml-2 mt-1"
            icon
            :loading="sendingMessage"
            @click="sendQuestion"
          >
            <v-icon
              size="x-large"
              icon="mdi-send-circle-outline"
            />
          </v-btn>
        </v-row>
      </v-card-text>
    </v-card>
  </v-container>
</template>
