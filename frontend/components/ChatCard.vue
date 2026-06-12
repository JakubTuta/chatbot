<script setup lang="ts">
import type { WebsocketMessage, WebsocketResponse } from '~/constants/websocket'
import type { IContainer } from '~/models/container'
import { marked } from 'marked'
import { getWebsocket } from '~/constants/websocket'

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
const messagesContainer = ref<HTMLDivElement | null>(null)
const waitingForResponse = ref(false)
const useStructuredOutput = ref(false)
const structuredOutputFormat = ref([])
const isFormValid = ref(false)
const expandedThoughts = ref<Record<number, boolean>>({})
const botThoughtsVisible = ref(false)
const copiedIndex = ref<string | null>(null)
const showScrollFab = ref(false)

const userMessageColor = 'rgb(var(--v-theme-chat-user))'
const botMessageColor = 'rgb(var(--v-theme-chat-bot))'

const splitMessageCache = new Map<string, ReturnType<typeof splitMessageRaw>>()

const chatStore = useChatStore()
const { chatHistoryPerModel, aiModels } = storeToRefs(chatStore)

const containerStore = useContainerStore()
const { containers } = storeToRefs(containerStore)

const snackbarStore = useSnackbarStore()

const isReconnecting = ref(false)

const suggestions = [
  'Explain quantum computing simply',
  'Write a Python quicksort function',
  'Give me some productivity tips',
  'Summarize the history of the internet',
]

const modelStatusLabel = computed(() => {
  if (!selectedModel.value)
    return null
  const status = selectedModel.value.status
  if (status === 'running')
    return { text: 'Running', color: 'success' }
  if (status === 'pulling_model')
    return { text: 'Pulling…', color: 'warning' }
  if (status === 'exited')
    return { text: 'Stopped', color: 'error' }

  return { text: status, color: 'grey' }
})

const canSend = computed(() => !!selectedModel.value
  && selectedModel.value.status === 'running'
  && !!message.value.trim()
  && !!selectedChatId.value
  && !!websocket.value
  && !waitingForResponse.value
  && !isReconnecting.value,
)

onUnmounted(() => {
  if (websocket.value)
    websocket.value.closeConnection()
})

const chatHistory = computed(() => {
  if (!selectedModel.value || !chatHistoryPerModel.value[selectedModel.value.model])
    return []

  return chatHistoryPerModel.value[selectedModel.value.model]
})

watch(chatHistory, () => {
  nextTick(() => {
    scrollToBottom()
  })
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
  if (!newValue.length) {
    selectedModel.value = null

    return
  }
  const stillExists = selectedModel.value
    && newValue.some(m => m.model === selectedModel.value!.model
      && m.parameters === selectedModel.value!.parameters)
  if (!stillExists)
    selectedModel.value = newValue[0]
}, { immediate: true })

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

const activeChatId = ref('')

const websocketHandlers = {
  onConnect: () => {
    isReconnecting.value = false
    // eslint-disable-next-line no-console
    console.log(`Connected to room ${selectedChatId.value}`)
  },

  onDisconnect: () => {
    waitingForResponse.value = false
    // eslint-disable-next-line no-console
    console.log(`Disconnected from room ${selectedChatId.value}`)
  },

  onReconnecting: (attempt: number) => {
    isReconnecting.value = true
    // eslint-disable-next-line no-console
    console.log(`Reconnecting... attempt ${attempt}`)
  },

  onError: (errorMessage: string) => {
    waitingForResponse.value = false
    snackbarStore.showSnackbarError(errorMessage)
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
    if (selectedChatId.value !== activeChatId.value)
      return

    waitingForResponse.value = false
    if (message.done) {
      if (selectedModel.value) {
        chatHistoryPerModel.value[selectedModel.value.model].push({
          role: 'assistant',
          content: message.message,
          image: '',
        })
      }
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

  activeChatId.value = newChatId

  if (websocket.value)
    websocket.value.closeConnection()

  websocket.value = getWebsocket(websocketHandlers, newChatId)
}, { immediate: true })

function softReset() {
  message.value = ''
  image.value = ''
  botResponse.value = ''
  splitMessageCache.clear()
  emit('softReset')
}

function copyToClipboard(content: string, key?: string) {
  navigator.clipboard.writeText(content)
  if (key !== undefined) {
    copiedIndex.value = key
    setTimeout(() => {
      copiedIndex.value = null
    }, 1500)
  }
}

function useSuggestion(text: string) {
  message.value = text
  focusComposer()
  nextTick(() => {
    if (composerTextarea.value)
      autoGrow(composerTextarea.value)
  })
}

function onMessagesScroll() {
  const el = messagesContainer.value
  if (!el)
    return
  showScrollFab.value = el.scrollHeight - el.scrollTop - el.clientHeight > 120
}

function splitMessage(message: string) {
  if (splitMessageCache.has(message))
    return splitMessageCache.get(message)!

  const result = splitMessageRaw(message)
  splitMessageCache.set(message, result)

  return result
}

function splitMessageRaw(message: string) {
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
  const emptyTagRegex = /<([a-z0-9]+)(\s[^>]*)?>(\s*)<\/\1>/gi

  let previousText = ''
  let currentText = text

  while (previousText !== currentText) {
    previousText = currentText
    currentText = currentText.replace(emptyTagRegex, '')
  }

  return currentText
}

marked.use({ gfm: true, breaks: true })

function renderMarkdown(text: string): string {
  return marked.parse(text) as string
}

const composerTextarea = ref<HTMLTextAreaElement | null>(null)

function autoGrow(el: HTMLTextAreaElement) {
  el.style.height = 'auto'
  el.style.height = `${Math.min(el.scrollHeight, 128)}px`
}

function onTextareaInput(event: Event) {
  autoGrow(event.target as HTMLTextAreaElement)
}

function focusComposer() {
  composerTextarea.value?.focus()
}

function toggleThoughts(index: number) {
  expandedThoughts.value[index] = !expandedThoughts.value[index]
}

function sendQuestion() {
  if (!canSend.value)
    return

  if (!websocket.value || websocket.value.readyState !== WebSocket.OPEN) {
    snackbarStore.showSnackbarError('Connection lost — please wait for reconnection or refresh the page.')

    return
  }

  waitingForResponse.value = true

  const model = selectedModel.value!.model
  const modelParameters = selectedModel.value!.parameters

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
  <div class="chat-card">
    <!-- Controls: model select + structured output -->
    <div class="chat-controls">
      <div class="controls-row">
        <v-select
          v-model="selectedModel"
          label="AI Model"
          :items="userPulledModels"
          :item-title="item => `${item.name} - ${item.parameters}`"
          return-object
          density="comfortable"
          hide-details
          class="model-select"
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

          <template
            v-if="modelStatusLabel"
            #append-inner
          >
            <v-chip
              :color="modelStatusLabel.color"
              size="x-small"
              variant="tonal"
              class="mr-1"
            >
              {{ modelStatusLabel.text }}
            </v-chip>
          </template>
        </v-select>

        <div class="structured-output-control">
          <v-btn
            size="small"
            :variant="useStructuredOutput && canUseStructuredOutput
              ? 'tonal'
              : 'outlined'"
            :color="useStructuredOutput && canUseStructuredOutput
              ? 'primary'
              : undefined"
            prepend-icon="mdi-code-json"
          >
            JSON format
            <StructuredOutputSelector
              v-model:format="structuredOutputFormat"
              v-model:is-form-valid="isFormValid"
            />

            <v-tooltip
              activator="parent"
              location="top"
            >
              When enabled, AI model returns a response in the given JSON format.
            </v-tooltip>
          </v-btn>

          <v-switch
            v-model="useStructuredOutput"
            :disabled="!canUseStructuredOutput"
            density="compact"
            color="primary"
            hide-details
            class="ml-4"
          />
        </div>
      </div>

      <v-alert
        v-if="selectedModel && selectedModel.status !== 'running'"
        type="warning"
        density="compact"
        variant="tonal"
        class="text-body-2 mt-2"
      >
        <span v-if="selectedModel.status === 'pulling_model'">
          Model is still being pulled — sending will be enabled once it's ready.
        </span>

        <span v-else>
          Container is not running.
          <v-btn
            variant="text"
            size="x-small"
            class="px-1"
            to="/models"
          >
            Manage on Models page
          </v-btn>
        </span>
      </v-alert>

      <v-alert
        v-if="isReconnecting"
        type="warning"
        density="compact"
        variant="tonal"
        class="mt-2"
      >
        Connection lost — reconnecting...
      </v-alert>
    </div>

    <!-- Messages area wrapper -->
    <div class="messages-area">
      <div
        ref="messagesContainer"
        class="messages-container"
        @scroll="onMessagesScroll"
      >
        <!-- Empty: no model -->
        <div
          v-if="!selectedModel"
          class="empty-state"
        >
          <div class="empty-state-icon-wrap mb-5">
            <v-icon
              size="40"
              icon="mdi-robot-outline"
              color="white"
            />
          </div>

          <div class="text-h6 font-weight-medium mb-2">
            No model is running yet
          </div>

          <v-timeline
            align="start"
            density="compact"
            class="text-left"
            style="max-width: 380px"
          >
            <v-timeline-item
              dot-color="primary"
              size="x-small"
            >
              <div class="text-body-2">
                Make sure <strong>Docker Desktop</strong> is running.
              </div>
            </v-timeline-item>

            <v-timeline-item
              dot-color="primary"
              size="x-small"
            >
              <div class="text-body-2">
                Go to the
                <v-btn
                  variant="text"
                  size="x-small"
                  class="px-1"
                  to="/models"
                >
                  Models page
                </v-btn>
                ,
                pick a model, select a version, and click <strong>Create container</strong>.
              </div>
            </v-timeline-item>

            <v-timeline-item
              dot-color="success"
              size="x-small"
            >
              <div class="text-body-2">
                Once the status shows <strong>Running</strong>, come back here and start chatting.
              </div>
            </v-timeline-item>
          </v-timeline>
        </div>

        <!-- Empty: model ready but no messages -->
        <div
          v-if="!chatHistory.length && !botResponse && !waitingForResponse && selectedModel"
          class="empty-state"
        >
          <div class="empty-state-icon-wrap mb-5">
            <v-icon
              size="40"
              icon="mdi-chat-outline"
              color="white"
            />
          </div>

          <div class="text-h6 font-weight-medium mb-1">
            Start the conversation
          </div>

          <div class="text-body-2 text-medium-emphasis mb-6">
            Type a message below or try a suggestion
          </div>

          <div class="suggestions-row">
            <v-chip
              v-for="s in suggestions"
              :key="s"
              variant="tonal"
              color="primary"
              class="suggestion-chip"
              @click="useSuggestion(s)"
            >
              {{ s }}
            </v-chip>
          </div>
        </div>

        <!-- Messages list with enter transitions -->
        <TransitionGroup
          name="msg"
          tag="div"
          class="messages-list"
        >
          <!-- Historical messages -->
          <div
            v-for="(chatMessage, index) in chatHistory"
            :key="index"
            class="message-row"
            :class="chatMessage.role === 'user'
              ? 'message-row--user'
              : 'message-row--bot'"
          >
            <!-- Bot avatar -->
            <v-avatar
              v-if="chatMessage.role === 'assistant'"
              size="28"
              class="message-avatar"
              style="background: linear-gradient(135deg, #6366F1, #818CF8); flex-shrink: 0"
            >
              <v-icon
                size="16"
                color="white"
              >
                mdi-robot
              </v-icon>
            </v-avatar>

            <!-- Message bubble -->
            <div
              class="message-bubble"
              :class="chatMessage.role === 'user'
                ? 'message-bubble--user'
                : 'message-bubble--bot'"
              :style="chatMessage.role === 'user'
                ? `background-color: ${userMessageColor}`
                : `background-color: ${botMessageColor}`"
            >
              <!-- Bot content -->
              <template v-if="chatMessage.role === 'assistant'">
                <v-btn
                  v-if="splitMessage(chatMessage.content).thoughts"
                  size="x-small"
                  variant="tonal"
                  class="mb-2"
                  @click="toggleThoughts(index)"
                >
                  {{ expandedThoughts[index]
                    ? 'Hide thoughts'
                    : 'Show thoughts' }}
                </v-btn>

                <div
                  v-if="splitMessage(chatMessage.content).thoughts && expandedThoughts[index]"
                  class="text-body-2 mb-2 font-italic"
                  style="white-space: pre-wrap; opacity: 0.8"
                >
                  {{ splitMessage(chatMessage.content).thoughts }}
                </div>

                <div
                  v-for="(part, partIndex) in splitMessage(chatMessage.content).parts"
                  :key="partIndex"
                >
                  <div
                    v-if="part.title === 'text'"
                    v-sanitize-html="renderMarkdown(part.content)"
                    class="markdown-body"
                  />

                  <div
                    v-else-if="part.title === 'code'"
                    class="my-3"
                  >
                    <v-card>
                      <v-card-title
                        class="text-subtitle-2"
                        style="display: flex; justify-content: space-between; align-items: center; background-color: rgba(127, 127, 127, 0.15)"
                      >
                        <span>{{ part.language || 'code' }}</span>

                        <v-btn
                          variant="text"
                          size="x-small"
                          :icon="copiedIndex === `code-${index}-${partIndex}`
                            ? 'mdi-check'
                            : 'mdi-content-copy'"
                          @click="copyToClipboard(part.content, `code-${index}-${partIndex}`)"
                        />
                      </v-card-title>

                      <v-card-text class="code-text mt-2">
                        {{ part.content }}
                      </v-card-text>
                    </v-card>
                  </div>
                </div>
              </template>

              <!-- User content -->
              <template v-else>
                {{ chatMessage.content }}
              </template>

              <!-- Attached image -->
              <p
                v-if="chatMessage.image"
                align="end"
                class="mb-0 mt-2"
              >
                <img
                  :src="chatMessage.image"
                  alt="Uploaded image"
                  style="max-width: 100%; max-height: 120px; border-radius: 8px"
                >
              </p>
            </div>

            <!-- Hover-reveal copy action -->
            <v-btn
              class="message-action-btn"
              icon
              size="x-small"
              variant="plain"
              @click="copyToClipboard(chatMessage.content, `msg-${index}`)"
            >
              <v-icon size="14">
                {{ copiedIndex === `msg-${index}`
                  ? 'mdi-check'
                  : 'mdi-content-copy' }}
              </v-icon>
            </v-btn>

            <!-- User avatar -->
            <v-avatar
              v-if="chatMessage.role === 'user'"
              size="28"
              class="message-avatar"
              style="background: linear-gradient(135deg, #4F46E5, #6366F1); flex-shrink: 0"
            >
              <v-icon
                size="16"
                color="white"
              >
                mdi-account
              </v-icon>
            </v-avatar>
          </div>

          <!-- Streaming bot response -->
          <div
            v-if="botResponse"
            key="streaming"
            class="message-row message-row--bot"
          >
            <v-avatar
              size="28"
              class="message-avatar"
              style="background: linear-gradient(135deg, #6366F1, #818CF8); flex-shrink: 0"
            >
              <v-icon
                size="16"
                color="white"
              >
                mdi-robot
              </v-icon>
            </v-avatar>

            <div
              class="message-bubble message-bubble--bot"
              :style="`background-color: ${botMessageColor}`"
            >
              <v-btn
                v-if="splitMessage(botResponse).thoughts"
                size="x-small"
                variant="tonal"
                class="mb-2"
                @click="botThoughtsVisible = !botThoughtsVisible"
              >
                {{ botThoughtsVisible
                  ? 'Hide thoughts'
                  : 'Show thoughts' }}
              </v-btn>

              <div
                v-if="splitMessage(botResponse).thoughts && botThoughtsVisible"
                class="text-body-2 mb-2 font-italic"
                style="white-space: pre-wrap; opacity: 0.8"
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
                  class="my-3"
                >
                  <v-card>
                    <v-card-title
                      class="text-subtitle-2"
                      style="display: flex; justify-content: space-between; align-items: center; background-color: rgba(127, 127, 127, 0.15)"
                    >
                      <span>{{ part.language }}</span>

                      <v-btn
                        size="x-small"
                        icon="mdi-content-copy"
                        @click="copyToClipboard(part.content)"
                      />
                    </v-card-title>

                    <v-card-text class="code-text mt-2">
                      {{ part.content }}
                    </v-card-text>
                  </v-card>
                </div>
              </div>

              <!-- Blinking caret during streaming -->
              <span class="stream-caret" />
            </div>
          </div>

          <!-- Typing indicator -->
          <div
            v-if="waitingForResponse"
            key="typing"
            class="message-row message-row--bot"
          >
            <v-avatar
              size="28"
              class="message-avatar"
              style="background: linear-gradient(135deg, #6366F1, #818CF8); flex-shrink: 0"
            >
              <v-icon
                size="16"
                color="white"
              >
                mdi-robot
              </v-icon>
            </v-avatar>

            <div
              class="message-bubble message-bubble--bot typing-bubble"
              :style="`background-color: ${botMessageColor}`"
            >
              <div class="typing-indicator">
                <span />

                <span />

                <span />
              </div>
            </div>
          </div>
        </TransitionGroup>

        <div ref="scrollToMe" />
      </div>

      <!-- Scroll-to-bottom FAB -->
      <Transition name="fade">
        <v-btn
          v-if="showScrollFab"
          class="scroll-fab"
          icon
          size="small"
          elevation="4"
          style="background: linear-gradient(135deg, #6366F1, #818CF8)"
          @click="scrollToBottom"
        >
          <v-icon color="white">
            mdi-chevron-down
          </v-icon>
        </v-btn>
      </Transition>
    </div>

    <!-- Composer bar -->
    <div
      class="composer-bar"
      :class="{'composer-disabled': !selectedModel || selectedModel.status !== 'running' || waitingForResponse}"
    >
      <div
        v-if="image"
        class="composer-image-preview"
      >
        <v-badge
          icon="mdi-close"
          color="error"
          style="cursor: pointer"
          @click="clearImage"
        >
          <img
            :src="image"
            alt="Uploaded image"
            style="max-height: 80px; border-radius: 8px"
          >
        </v-badge>
      </div>

      <div class="composer-row">
        <v-btn
          v-if="selectedModel?.canProcessImages"
          icon
          variant="text"
          size="small"
          :disabled="!selectedModel || selectedModel.status !== 'running' || waitingForResponse"
          @click="fileInput?.click()"
        >
          <v-icon>mdi-image-plus</v-icon>

          <input
            ref="fileInput"
            type="file"
            accept="image/*"
            style="display: none"
            @change="handleImageUpload"
          >
        </v-btn>

        <div
          class="composer-input-wrap"
          @click="focusComposer"
        >
          <textarea
            ref="composerTextarea"
            v-model="message"
            placeholder="Message…"
            rows="1"
            class="composer-native-textarea"
            :disabled="!selectedModel || selectedModel.status !== 'running' || waitingForResponse"
            @input="onTextareaInput"
            @keydown.enter.exact.prevent="sendQuestion"
            @keydown.shift.enter.exact.stop
          />
        </div>

        <v-btn
          icon
          variant="text"
          size="small"
          :disabled="!canSend"
          class="send-btn"
          :class="{'send-btn--active': canSend}"
          @click="sendQuestion"
        >
          <v-icon>mdi-send</v-icon>
        </v-btn>
      </div>
    </div>
  </div>
</template>

<style scoped>
.chat-card {
  display: flex;
  flex-direction: column;
  gap: 12px;
  width: 100%;
  height: 100%;
  min-height: 0;
}

.controls-row {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  flex-wrap: wrap;
}

.model-select {
  min-width: 180px;
  flex: 1;
  max-width: 340px;
}

.structured-output-control {
  display: flex;
  align-items: center;
  padding-top: 4px;
  flex-shrink: 0;
}

/* ── Messages area ─────────────────────────────────────── */
.messages-area {
  position: relative;
  flex: 1;
  min-height: 0;
}

.messages-container {
  height: 100%;
  overflow-y: auto;
  padding: 16px 0;
  display: flex;
  flex-direction: column;
  scrollbar-width: thin;
  scrollbar-color: rgba(127, 127, 127, 0.25) transparent;
}

.messages-container::-webkit-scrollbar {
  width: 4px;
}

.messages-container::-webkit-scrollbar-track {
  background: transparent;
}

.messages-container::-webkit-scrollbar-thumb {
  background: rgba(127, 127, 127, 0.25);
  border-radius: 2px;
}

.messages-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* ── Empty states ──────────────────────────────────────── */
.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 16px;
  text-align: center;
}

.empty-state-icon-wrap {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  background: linear-gradient(135deg, #6366F1, #818CF8);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 20px rgba(99, 102, 241, 0.35);
}

.suggestions-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
  max-width: 480px;
}

.suggestion-chip {
  cursor: pointer;
  transition: transform 0.15s ease, opacity 0.15s ease;
}

.suggestion-chip:hover {
  transform: translateY(-2px);
}

/* ── Message rows ──────────────────────────────────────── */
.message-row {
  display: flex;
  align-items: flex-end;
  gap: 8px;
}

.message-row--user {
  justify-content: flex-end;
}

.message-row--bot {
  justify-content: flex-start;
}

.message-avatar {
  flex-shrink: 0;
  margin-bottom: 2px;
}

/* hover-reveal copy button */
.message-row--user .message-action-btn {
  order: -1;
}

.message-action-btn {
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.15s ease;
  flex-shrink: 0;
  align-self: flex-end;
  margin-bottom: 2px;
}

.message-row:hover .message-action-btn {
  opacity: 1;
  pointer-events: auto;
}

/* ── Bubbles ───────────────────────────────────────────── */
.message-bubble {
  border-radius: 18px;
  padding: 10px 16px;
  font-size: 0.925rem;
  line-height: 1.65;
  word-break: break-word;
  max-width: 72%;
}

.message-bubble--user {
  border-bottom-right-radius: 4px;
  color: #ffffff;
  box-shadow: 0 2px 12px rgba(99, 102, 241, 0.3);
}

.message-bubble--bot {
  border-bottom-left-radius: 4px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
}

.typing-bubble {
  padding: 14px 18px 10px;
}

/* ── Typing indicator ──────────────────────────────────── */
.typing-indicator {
  display: flex;
  align-items: flex-end;
  gap: 5px;
  height: 22px;
}

.typing-indicator span {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: rgba(var(--v-theme-on-surface), 0.5);
  animation: typing-bounce 1.2s infinite ease-in-out;
  flex-shrink: 0;
}

.typing-indicator span:nth-child(1) { animation-delay: 0s; }
.typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
.typing-indicator span:nth-child(3) { animation-delay: 0.4s; }

@keyframes typing-bounce {
  0%, 60%, 100% { transform: translateY(0); opacity: 0.45; }
  30% { transform: translateY(-6px); opacity: 1; }
}

/* ── Stream caret ──────────────────────────────────────── */
.stream-caret {
  display: inline-block;
  width: 2px;
  height: 1em;
  background-color: currentColor;
  margin-left: 2px;
  vertical-align: text-bottom;
  animation: caret-blink 1s step-end infinite;
}

@keyframes caret-blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

/* ── Scroll FAB ────────────────────────────────────────── */
.scroll-fab {
  position: absolute;
  bottom: 16px;
  right: 16px;
  z-index: 5;
}

/* ── TransitionGroup: message entrance ─────────────────── */
.msg-enter-active {
  transition: opacity 0.25s ease, transform 0.25s ease;
}

.msg-enter-from {
  opacity: 0;
  transform: translateY(10px);
}

.msg-enter-to {
  opacity: 1;
  transform: translateY(0);
}

/* ── Fade (FAB show/hide) ──────────────────────────────── */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* ── Reduced motion ────────────────────────────────────── */
@media (prefers-reduced-motion: reduce) {
  .msg-enter-active {
    transition: opacity 0.15s ease;
  }

  .msg-enter-from {
    transform: none;
  }

  .stream-caret {
    animation: none;
    opacity: 1;
  }

  .typing-indicator span {
    animation: none;
    opacity: 0.6;
  }

  .suggestion-chip:hover {
    transform: none;
  }
}

/* ── Code blocks ───────────────────────────────────────── */
.code-text {
  white-space: pre-wrap;
  font-family: 'JetBrains Mono', 'Consolas', 'Menlo', monospace;
  font-size: 0.875rem;
}

/* ── Composer ──────────────────────────────────────────── */
.composer-bar {
  border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  border-radius: 16px;
  padding: 6px 8px 6px 16px;
  background: rgb(var(--v-theme-surface-2));
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
  flex-shrink: 0;
}

.composer-bar:focus-within {
  border-color: #6366F1;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.12);
}

.composer-disabled {
  opacity: 0.65;
}

.composer-row {
  display: flex;
  align-items: flex-end;
  gap: 4px;
}

.composer-input-wrap {
  flex: 1;
  min-width: 0;
  cursor: text;
}

.composer-native-textarea {
  width: 100%;
  resize: none;
  border: none;
  outline: none;
  background: transparent;
  font: inherit;
  font-size: 0.9375rem;
  line-height: 1.5;
  padding: 8px 0;
  color: inherit;
  min-height: 40px;
  max-height: 128px;
  overflow-y: auto;
  display: block;
}

.composer-native-textarea::placeholder {
  color: rgba(var(--v-theme-on-surface), 0.45);
}

.composer-native-textarea:disabled {
  cursor: not-allowed;
}

.composer-image-preview {
  padding: 8px 0 4px 4px;
  display: flex;
  justify-content: flex-end;
}

/* Send button */
.send-btn {
  transition: transform 0.15s ease;
}

.send-btn--active {
  color: #6366F1 !important;
}

.send-btn--active:active {
  transform: scale(0.88);
}

/* ── Markdown ──────────────────────────────────────────── */
.markdown-body :deep(p) {
  margin: 0.3em 0;
}

.markdown-body :deep(p:first-child) {
  margin-top: 0;
}

.markdown-body :deep(p:last-child) {
  margin-bottom: 0;
}

.markdown-body :deep(h1),
.markdown-body :deep(h2),
.markdown-body :deep(h3),
.markdown-body :deep(h4) {
  font-weight: 600;
  line-height: 1.3;
  margin: 0.75em 0 0.3em;
}

.markdown-body :deep(h1:first-child),
.markdown-body :deep(h2:first-child),
.markdown-body :deep(h3:first-child) {
  margin-top: 0;
}

.markdown-body :deep(h1) { font-size: 1.35em; }
.markdown-body :deep(h2) { font-size: 1.2em; }
.markdown-body :deep(h3) { font-size: 1.08em; }
.markdown-body :deep(h4) { font-size: 1em; }

.markdown-body :deep(ul),
.markdown-body :deep(ol) {
  padding-left: 1.5em;
  margin: 0.4em 0;
}

.markdown-body :deep(li) {
  margin: 0.2em 0;
}

.markdown-body :deep(strong) {
  font-weight: 600;
}

.markdown-body :deep(em) {
  font-style: italic;
}

.markdown-body :deep(code) {
  font-family: 'JetBrains Mono', 'Consolas', 'Menlo', monospace;
  font-size: 0.85em;
  background: rgba(127, 127, 127, 0.2);
  padding: 0.1em 0.35em;
  border-radius: 4px;
}

.markdown-body :deep(blockquote) {
  border-left: 3px solid rgba(127, 127, 127, 0.4);
  padding-left: 12px;
  margin: 0.5em 0;
  opacity: 0.85;
}

.markdown-body :deep(hr) {
  border: none;
  border-top: 1px solid rgba(127, 127, 127, 0.3);
  margin: 0.75em 0;
}

.markdown-body :deep(a) {
  color: inherit;
  text-decoration: underline;
  opacity: 0.9;
}

/* ── Mobile ────────────────────────────────────────────── */
@media (max-width: 600px) {
  .message-bubble {
    max-width: 85%;
  }

  .model-select {
    max-width: 100%;
    min-width: 0;
    flex-basis: 100%;
  }

  .message-action-btn {
    opacity: 1;
    pointer-events: auto;
  }
}
</style>
