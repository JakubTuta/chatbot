<script setup lang="ts">
const router = useRouter()

const isLoggedIn = ref(false)

function goToLogIn() {
  router.push('/auth/login')
}

function goToRegister() {
  router.push('/auth/register')
}

function goToModels() {
  router.push('/models')
}
</script>

<template>
  <div style="display: flex; align-items: center; justify-content: center; height: 100%">
    <div v-if="!isLoggedIn">
      <v-btn @click="goToLogIn">
        Login
      </v-btn>

      <v-btn
        class="mx-4"
        @click="goToRegister"
      >
        Register
      </v-btn>

      <v-btn @click="goToModels">
        Models
      </v-btn>
    </div>
  </div>
</template>
