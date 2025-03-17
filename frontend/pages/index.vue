<script setup lang="ts">
//
</script>

<template>
  <v-container style="display: flex; align-items: center; justify-content: center; height: 100%">
    <div
      class="text-h5"
    >
      <p class="text-h4 py-3">
        Welcome to Chatbot!
      </p>

      <p class="py-3">
        Chatbot is a platform that enables seamless interaction with AI models locally through Ollama. This application simplifies the management of Docker containers hosting these models, allowing you to chat with various AI models without sending your data to external services. Experience the power of local AI with easy container management and a user-friendly interface.
      </p>

      <p class="py-3">
        To get started,

        <NuxtLink to="/auth/login">
          <v-btn
            variant="text"
            color="primary"
            class="mx-2"
          >
            Login
          </v-btn>
        </NuxtLink>

        or

        <NuxtLink to="/auth/register">
          <v-btn
            variant="text"
            color="primary"
            class="mx-2"
          >
            Register
          </v-btn>
        </NuxtLink>
      </p>

      <p class="py-3">
        You can also check out
        <NuxtLink to="/models">
          <v-btn
            variant="text"
            color="primary"
            class="mx-2"
          >
            Models
          </v-btn>
        </NuxtLink>

        to see the available AI models.
      </p>

      <p class="py-3">
        Go straight to
        <NuxtLink to="/chat">
          <v-btn
            variant="text"
            color="primary"
            class="mx-2"
          >
            Chat
          </v-btn>
        </NuxtLink>
      </p>
    </div>
  </v-container>
</template>
