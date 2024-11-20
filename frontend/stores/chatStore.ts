export const useChatStore = defineStore('chat', () => {
  const aiModels = ref<{ name: string, model: string }[]>([])
  const chatHistoryPerModel = ref<{ [model: string]: { role: 'user' | 'assistant', content: string }[] }>({})
  const allChats = ref<{ [model: string]: { id: string, title: string }[] }>({})

  const sendingMessage = ref(false)

  const apiStore = useApiStore()
  const authStore = useAuthStore()
  const { api } = storeToRefs(apiStore)

  const resetState = () => {
    aiModels.value = []
    chatHistoryPerModel.value = {}
    sendingMessage.value = false
  }

  const postRequest = async (url: string, data: any) => {
    if (!(await authStore.areTokensValid())) {
      authStore.logOut()

      return null
    }

    try {
      const response = await api.value.post(url, data)

      if (response.status === 401) {
        authStore.logOut()
      }

      return response
    }
    catch (error) {
      console.error(error)
    }

    return null
  }

  const getRequest = async (url: string, params: any) => {
    if (!(await authStore.areTokensValid())) {
      authStore.logOut()

      return null
    }

    try {
      const response = await api.value.get(url, { params })

      if (response.status === 401) {
        authStore.logOut()
      }

      return response
    }
    catch (error) {
      console.error(error)
    }

    return null
  }

  const fetchAIModels = async () => {
    const url = 'ai-models/'

    const response = await getRequest(url, {})

    if (response?.status === 200) {
      aiModels.value = response.data
    }
  }

  const fetchAllChats = async (model: string) => {
    const url = `all-chats/${model}`

    const response = await getRequest(url, { model })

    if (response?.status === 200) {
      allChats.value[model] = response.data
    }
  }

  const fetchChatHistory = async (model: string, chatId: string) => {
    const url = `chat-history/${model}/${chatId}`

    const response = await getRequest(url, { model })

    if (response?.status === 200) {
      chatHistoryPerModel.value[model] = response.data
    }
  }

  const askBot = async (model: string, message: string) => {
    const url = `ask-bot/${model}`

    sendingMessage.value = true

    chatHistoryPerModel.value[model].push({
      role: 'user',
      content: message,
    })

    const response = await postRequest(url, { model, message })

    if (response?.status === 200) {
      chatHistoryPerModel.value[model].push({
        role: 'assistant',
        content: response.data.content,
      })
    }

    sendingMessage.value = false
  }

  const createChat = async (model: string) => {
    const url = `all-chats/${model}`

    const response = await postRequest(url, {})

    if (response?.status === 201) {
      const { id, title } = response.data
      allChats.value[model].push({ id, title })
    }
  }

  const deleteChat = async (model: string, chatId: string) => {
    const url = `all-chats/${model}`

    if (!(await authStore.areTokensValid())) {
      authStore.logOut()

      return
    }

    try {
      const response = await api.value.delete(url, { data: { chat_id: chatId } })

      if (response.status === 200) {
        allChats.value[model] = allChats.value[model].filter(chat => chat.id !== chatId)
      }
      else if (response.status === 401) {
        authStore.logOut()
      }
    }
    catch (error) {
      console.error(error)
    }
  }

  const changeChatTitle = async (model: string, chat: { id: string }, newTitle: string) => {
    const url = `all-chats/${model}`

    if (!(await authStore.areTokensValid())) {
      authStore.logOut()

      return
    }

    try {
      const response = await api.value.put(url, { id: chat.id, title: newTitle })

      if (response.status === 200) {
        const foundChat = allChats.value[model].find(e => e.id === chat.id)
        if (foundChat) {
          foundChat.title = newTitle
          allChats.value[model] = [foundChat, ...allChats.value[model].filter(e => e.id !== chat.id)]
        }
      }
      else if (response.status === 401) {
        authStore.logOut()
      }
    }
    catch (error) {
      console.error(error)
    }
  }

  return {
    aiModels,
    chatHistoryPerModel,
    allChats,
    sendingMessage,
    resetState,
    fetchAIModels,
    fetchAllChats,
    fetchChatHistory,
    askBot,
    createChat,
    deleteChat,
    changeChatTitle,
  }
})
