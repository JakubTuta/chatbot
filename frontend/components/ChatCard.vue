<script setup lang="ts">
import { useDisplay } from 'vuetify';
import { type WebsocketMessage, type WebsocketResponse, getWebsocket } from '~/constants/websocket';
import type { IContainer } from '~/models/container';

const props = defineProps<{
  selectedChatId: string
  reset: boolean
}>()

const emit = defineEmits<{
  (e: 'softReset'): void
}>()

const selectedModel = defineModel<IContainer | null>('selectedModel', { default: null, required: true })

const { selectedChatId, reset } = toRefs(props)

const message = ref('')
const image = ref('')
const botResponse = ref('')
const fileInput = ref<HTMLInputElement | null>(null)
const websocket = ref<WebSocketWrapper | null>(null)
const scrollToMe = ref<HTMLDivElement | null>(null)
const waitingForResponse = ref(false)
const useStructuredOutput = ref(false)
const structuredOutputFormat = ref([])
const isFormValid = ref(false)
const expandedThoughts = ref<Record<number, boolean>>({})
const botThoughtsVisible = ref(false)

const userMessageColor = '#168AFF'
const botMessageColor = '#9F33FF'

const { height, mobile } = useDisplay()

const chatStore = useChatStore()
const { chatHistoryPerModel, aiModels } = storeToRefs(chatStore)

const containerStore = useContainerStore()
const { containers } = storeToRefs(containerStore)

onUnmounted(() => {
  if (websocket.value)
    websocket.value.closeConnection()
})

const chatHistory = computed(() => {
  if (!selectedModel.value || !chatHistoryPerModel.value[selectedModel.value.model])
    return []

  // eslint-disable-next-line vue/no-async-in-computed-properties
  setTimeout(() => {
    scrollToBottom()
  }, 1000)

  return chatHistoryPerModel.value[selectedModel.value.model]
})

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
    } as IContainer
  })
    .filter(e => e !== null)
    .sort((a, b) => a.value.localeCompare(b.value))
})

const canUseStructuredOutput = computed(() => (isFormValid.value && structuredOutputFormat.value.length > 0))

watch(userPulledModels, (newValue) => {
  if (newValue.length)
    selectedModel.value = newValue[0]
})

watch(selectedModel, (newModel, oldModel) => {
  if (!newModel
    || (newModel.model === (oldModel?.model || '')
      && newModel.parameters === (oldModel?.parameters || ''))) {
    return
  }

  softReset()

  containerStore.runContainer(newModel)
  chatStore.fetchAllChats(newModel.model)
}, { immediate: true })

watch(reset, (newValue) => {
  if (newValue) {
    softReset()
  }
})

watch(botResponse, () => {
  nextTick(() => {
    scrollToBottom()
  })
})

function scrollToBottom() {
  if (scrollToMe.value)
    scrollToMe.value.scrollIntoView({ behavior: 'smooth' })
}

const websocketHandlers = {
  onConnect: () => {
    // eslint-disable-next-line no-console
    console.log(`Connected to room ${selectedChatId.value}`)
  },

  onDisconnect: () => {
    // eslint-disable-next-line no-console
    console.log(`Disconnected from room ${selectedChatId.value}`)
  },

  onSendMessage: (message: WebsocketMessage) => {
    const model = selectedModel.value!.model

    if (!chatHistoryPerModel.value[model]) {
      chatHistoryPerModel.value[model] = []
    }

    chatHistoryPerModel.value[model].push({
      role: 'user',
      content: message.message,
      image: image.value,
    })

    softReset()
    scrollToBottom()
  },

  onReceiveMessage: (message: WebsocketResponse) => {
    waitingForResponse.value = false
    if (message.done) {
      chatHistoryPerModel.value[selectedModel.value!.model].push({
        role: 'assistant',
        content: message.message,
        image: '',
      })
      botResponse.value = ''
    }
    else {
      botResponse.value += message.message
    }
  },
}

watch(selectedChatId, (newChatId) => {
  if (!newChatId)
    return

  if (websocket.value)
    websocket.value.closeConnection()

  websocket.value = getWebsocket(websocketHandlers, newChatId)
}, { immediate: true })

function softReset() {
  message.value = ''
  image.value = ''
  botResponse.value = ''
  emit('softReset')
}

function copyToClipboard(content: string) {
  navigator.clipboard.writeText(content)
}

function splitMessage(message: string) {
  let thoughts = ''
  let remainingMessage = message

  const thinkTagStart = remainingMessage.indexOf('<think>')
  const thinkTagEnd = remainingMessage.indexOf('</think>')

  if (thinkTagStart !== -1 && thinkTagEnd !== -1) {
    thoughts = remainingMessage.substring(thinkTagStart + 7, thinkTagEnd).trim()
    remainingMessage = remainingMessage.substring(0, thinkTagStart) + remainingMessage.substring(thinkTagEnd + 8)
  }

  const parts = []
  while (remainingMessage.length > 0) {
    const codeBlockStart = remainingMessage.indexOf('```')

    if (codeBlockStart === -1) {
      if (remainingMessage) {
        const cleanedText = cleanEmptyHtmlTags(remainingMessage).trim()
        if (cleanedText)
          parts.push({ title: 'text', content: cleanedText })
      }
      break
    }

    if (codeBlockStart > 0) {
      const textContent = remainingMessage.substring(0, codeBlockStart)
      const cleanedText = cleanEmptyHtmlTags(textContent).trim()
      if (cleanedText)
        parts.push({ title: 'text', content: cleanedText })
    }

    const codeBlockEnd = remainingMessage.indexOf('```', codeBlockStart + 3)

    if (codeBlockEnd !== -1) {
      const fullCodeBlock = remainingMessage.substring(codeBlockStart, codeBlockEnd + 3)
      const programmingLanguage = fullCodeBlock.match(/```(.*)\n/)?.[1] || ''
      const code = fullCodeBlock.replace(/```(.*)\n|```$/g, '')

      parts.push({ title: 'code', content: code.trim(), language: programmingLanguage.trim() })
      remainingMessage = remainingMessage.substring(codeBlockEnd + 3)
    }
    else {
      const code = remainingMessage.substring(codeBlockStart + 3)
      const programmingLanguage = code.match(/^(.*)\n/)?.[1] || ''
      const codeContent = programmingLanguage
        ? code.substring(programmingLanguage.length + 1)
        : code

      parts.push({
        title: 'code',
        content: codeContent.trim(),
        language: programmingLanguage.trim(),
      })
      break
    }
  }

  return { thoughts, parts }
}

function cleanEmptyHtmlTags(text: string): string {
  // Remove empty HTML tags
  const emptyTagRegex = /<([a-z0-9]+)(\s[^>]*)?>(\s*)<\/\1>/gi

  let previousText = ''
  let currentText = text

  while (previousText !== currentText) {
    previousText = currentText
    currentText = currentText.replace(emptyTagRegex, '')
  }

  return currentText
}

function toggleThoughts(index: number) {
  expandedThoughts.value[index] = !expandedThoughts.value[index]
}

function sendQuestion() {
  if (!selectedModel.value || !message.value || !selectedChatId.value || !websocket.value)
    return

  waitingForResponse.value = true

  const model = selectedModel.value.model
  const modelParameters = selectedModel.value.parameters

  const websocketMessage: WebsocketMessage = {
    message: message.value,
    ai_model: model,
    ai_model_parameters: modelParameters,
  }

  if (image.value)
    websocketMessage.image = image.value

  if (canUseStructuredOutput.value && useStructuredOutput.value)
    websocketMessage.structured_output = structuredOutputFormat.value

  websocket.value.sendMessage(websocketMessage)

  message.value = ''
  image.value = ''
}

function clearImage() {
  image.value = ''
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

  scrollToBottom()
}

watch(waitingForResponse, (newValue) => {
  if (newValue) {
    nextTick(() => {
      scrollToBottom()
    })
  }
})
</script>

<template>
  <v-card>
    <v-card-text>
      <v-row class="justify-space-between flex">
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
              <v-list-item to="/models">
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

        <v-col
          cols="12"
          sm="5"
          md="4"
          class="flex"
        >
          <v-text-field label="Structured output">
            <StructuredOutputSelector
              v-model:format="structuredOutputFormat"
              v-model:is-form-valid="isFormValid"
            />

            <v-tooltip
              activator="parent"
              location="top"
            >
              When enabled, AI model will return the message in the given JSON format.
            </v-tooltip>
          </v-text-field>

          <v-switch
            v-model="useStructuredOutput"
            :disabled="!canUseStructuredOutput"
            class="ml-4"
            color="primary"
          />
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
            class="overflow-y-auto"
          >
            <div
              v-for="(chatMessage, index) in chatHistory"
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
                class="px-4 py-2 text-align-start"
              >
                <div v-if="chatMessage.role === 'assistant'">
                  <v-btn
                    v-if="splitMessage(chatMessage.content).thoughts"
                    size="x-small"
                    class="mb-2"
                    @click="toggleThoughts(index)"
                  >
                    {{ expandedThoughts[index]
                      ? 'Hide thoughts'
                      : 'Show thoughts' }}
                  </v-btn>

                  <div
                    v-if="splitMessage(chatMessage.content).thoughts && expandedThoughts[index]"
                    class="mb-2 font-italic"
                    style="white-space: pre-wrap"
                  >
                    {{ splitMessage(chatMessage.content).thoughts }}
                  </div>

                  <div
                    v-for="(part, partIndex) in splitMessage(chatMessage.content).parts"
                    :key="partIndex"
                  >
                    <div
                      v-if="part.title === 'text'"
                      v-sanitize-html="part.content"
                      style="white-space: pre-wrap"
                    />

                    <div
                      v-else-if="part.title === 'code'"
                      class="my-4"
                    >
                      <v-card>
                        <v-card-title
                          class="text-subtitle-2"
                          style="display: flex; justify-content: space-between; align-items: center; background-color: rgba(127, 127, 127, 0.4)"
                        >
                          <span>
                            {{ part.language }}
                          </span>

                          <v-btn
                            variant="text"
                            size="x-small"
                            icon="mdi-content-copy"
                            @click="copyToClipboard(part.content)"
                          />
                        </v-card-title>

                        <v-card-text
                          style="white-space: pre-wrap"
                          class="mt-3"
                        >
                          {{ part.content }}
                        </v-card-text>
                      </v-card>
                    </div>
                  </div>
                </div>

                <div v-else>
                  {{ chatMessage.content }}
                </div>

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

            <v-list-item
              v-if="botResponse"
              rounded="shaped"
              :style="`display: flex; justify-content: flex-start; background-color: ${botMessageColor}`"
              :max-width="mobile
                ? '90%'
                : '70%'"
              class="mt-4 px-4 py-2 text-align-start"
            >
              <div>
                <v-btn
                  v-if="splitMessage(botResponse).thoughts"
                  size="x-small"
                  class="mb-2"
                  @click="botThoughtsVisible = !botThoughtsVisible"
                >
                  {{ botThoughtsVisible
                    ? 'Hide thoughts'
                    : 'Show thoughts' }}
                </v-btn>

                <div
                  v-if="splitMessage(botResponse).thoughts && botThoughtsVisible"
                  class="mb-2 font-italic"
                  style="white-space: pre-wrap"
                >
                  {{ splitMessage(botResponse).thoughts }}
                </div>

                <div
                  v-for="(part, partIndex) in splitMessage(botResponse).parts"
                  :key="partIndex"
                >
                  <div
                    v-if="part.title === 'text'"
                    v-sanitize-html="part.content"
                    style="white-space: pre-wrap"
                  />

                  <div
                    v-else-if="part.title === 'code'"
                    class="my-4"
                  >
                    <v-card>
                      <v-card-title
                        class="text-subtitle-2"
                        style="display: flex; justify-content: space-between; align-items: center; background-color: rgba(127, 127, 127, 0.4)"
                      >
                        <span>
                          {{ part.language }}
                        </span>

                        <v-btn
                          size="x-small"
                          icon="mdi-content-copy"
                          @click="copyToClipboard(part.content)"
                        />
                      </v-card-title>

                      <v-card-text
                        style="white-space: pre-wrap"
                        class="mt-3"
                      >
                        {{ part.content }}
                      </v-card-text>
                    </v-card>
                  </div>
                </div>
              </div>
            </v-list-item>

            <v-list-item
              v-if="waitingForResponse"
              rounded="shaped"
              :style="`display: flex; justify-content: flex-start; background-color: ${botMessageColor}`"
              max-width="10%"
              class="d-flex mt-4 justify-center px-4 py-2"
            >
              <v-progress-circular
                indeterminate
                color="primary"
                size="24"
              />
            </v-list-item>

            <div ref="scrollToMe" />
          </v-list>

          <v-spacer class="mt-4" />

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
          @click="fileInput?.click()"
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
          :disabled="waitingForResponse"
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
</template>
