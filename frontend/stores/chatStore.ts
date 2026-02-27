import type { IAIModel } from '~/models/aiModel'
import { mapAIModel } from '~/models/aiModel'

export const useChatStore = defineStore('chat', () => {
  const aiModels = ref<IAIModel[]>([])
  const chatHistoryPerModel = ref<{
    [model: string]: {
      role: 'user' | 'assistant'
      content: string
      image: string
    }[]
  }>({})
  const allChats = ref<{ [model: string]: { id: string, title: string }[] }>({})

  const sendingMessage = ref(false)
  const loading = ref(false)

  const apiStore = useApiStore()
  const snackbarStore = useSnackbarStore()
  const { api } = storeToRefs(apiStore)

  const resetState = () => {
    aiModels.value = []
    chatHistoryPerModel.value = {}
    sendingMessage.value = false
  }

  const fetchAIModels = async () => {
    const url = 'ai-models/'

    loading.value = true

    try {
      const response = await api.value.get(url)

      if (response?.status === 200) {
        aiModels.value = response.data.map(mapAIModel)
      }
    }
    catch (error: any) {
      console.error(error)
      snackbarStore.showSnackbarError(error.response?.data?.error || 'Failed to load AI models.')
    }
    finally {
      loading.value = false
    }
  }

  const pullAIModels = async (minPullCount: number) => {
    const url = `ai-models/?minPullCount=${minPullCount}`

    loading.value = true

    try {
      const response = await api.value.put(url)

      if (response.status === 200)
        await fetchAIModels()
    }
    catch (error: any) {
      console.error(error)
      snackbarStore.showSnackbarError(error.response?.data?.error || 'Failed to pull AI models.')
    }
    finally {
      loading.value = false
    }
  }

  const fetchAllChats = async (model: string) => {
    const url = `all-chats/${model}`

    try {
      const response = await api.value.get(url, { params: { model } })

      if (response?.status === 200) {
        allChats.value[model] = response.data
      }
    }
    catch (error: any) {
      console.error(error)
      snackbarStore.showSnackbarError(error.response?.data?.error || 'Failed to load chats.')
    }
  }

  const fetchChatHistory = async (model: string, chatId: string) => {
    const url = `chat-history/${model}/${chatId}`

    try {
      const response = await api.value.get(url, { params: { model } })

      if (response?.status === 200) {
        chatHistoryPerModel.value[model] = response.data
      }
    }
    catch (error: any) {
      console.error(error)
      snackbarStore.showSnackbarError(error.response?.data?.error || 'Failed to load chat history.')
    }
  }

  const askBot = async (model: string, parameters: string, chatId: string, message: string, image: string) => {
    const url = `ask-bot/${model}/${chatId}?parameters=${parameters}`

    sendingMessage.value = true

    if (!chatHistoryPerModel.value[model]) {
      chatHistoryPerModel.value[model] = []
    }

    chatHistoryPerModel.value[model].push({
      role: 'user',
      content: message,
      image,
    })

    try {
      const response = await api.value.post(url, { model, message, image })

      if (response?.status === 200) {
        chatHistoryPerModel.value[model].push({
          role: 'assistant',
          content: response.data.content,
          image: '',
        })
      }
    }
    catch (error: any) {
      console.error(error)
      snackbarStore.showSnackbarError(error.response?.data?.error || 'Failed to get a response from the bot.')
    }
    finally {
      sendingMessage.value = false
    }
  }

  const createChat = async (model: string) => {
    const url = `all-chats/${model}`

    try {
      const response = await api.value.post(url, {})

      if (response?.status === 201) {
        const { id, title } = response.data

        if (!allChats.value[model]) {
          allChats.value[model] = []
        }

        allChats.value[model].push({ id, title })

        return id
      }
    }
    catch (error: any) {
      console.error(error)
      snackbarStore.showSnackbarError(error.response?.data?.error || 'Failed to create a new chat.')
    }

    return null
  }

  const deleteChat = async (model: string, chatId: string) => {
    const url = `all-chats/${model}`

    try {
      const response = await api.value.delete(url, { data: { chat_id: chatId } })

      if (response.status === 200) {
        if (!allChats.value[model]) {
          allChats.value[model] = []
        }

        allChats.value[model] = allChats.value[model].filter(chat => chat.id !== chatId)
      }
    }
    catch (error: any) {
      console.error(error)
      snackbarStore.showSnackbarError(error.response?.data?.error || 'Failed to delete the chat.')
    }
  }

  const changeChatTitle = async (model: string, chat: { id: string }, newTitle: string) => {
    const url = `all-chats/${model}`

    try {
      const response = await api.value.put(url, { id: chat.id, title: newTitle })

      if (response.status === 200) {
        if (!allChats.value[model]) {
          allChats.value[model] = []
        }

        const foundChat = allChats.value[model].find(e => e.id === chat.id)
        if (foundChat) {
          foundChat.title = newTitle
          allChats.value[model] = [foundChat, ...allChats.value[model].filter(e => e.id !== chat.id)]
        }
      }
    }
    catch (error: any) {
      console.error(error)
      snackbarStore.showSnackbarError(error.response?.data?.error || 'Failed to rename the chat.')
    }
  }

  return {
    aiModels,
    chatHistoryPerModel,
    allChats,
    sendingMessage,
    loading,
    resetState,
    fetchAIModels,
    pullAIModels,
    fetchAllChats,
    fetchChatHistory,
    askBot,
    createChat,
    deleteChat,
    changeChatTitle,
  }
})
