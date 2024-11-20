<script setup lang="ts">
const router = useRouter()

const isLoggedIn = ref(false)

function goToLogIn() {
  router.push('/auth/login')
}

function goToRegister() {
  router.push('/auth/register')
}
</script>

<template>
  <div style="display: flex; align-items: center; justify-content: center; height: 100%">
    <div v-if="!isLoggedIn">
      <v-btn
        class="mr-4"
        @click="goToLogIn"
      >
        Login
      </v-btn>

      <v-btn @click="goToRegister">
        Register
      </v-btn>
    </div>
  </div>
</template>
