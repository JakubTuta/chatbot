<script setup lang="ts">
const router = useRouter()

const authStore = useAuthStore()
const { loading } = storeToRefs(authStore)

const username = ref('')
const password = ref('')
const isShowPassword = ref(false)

function goBack() {
  router.push('/')
}

function register() {
  authStore.register(username.value, password.value)
}
</script>

<template>
  <div style="display: flex; align-items: center; justify-content: center; height: 100%">
    <v-btn
      style="position: absolute; top: 20px; left: 20px;"
      prepend-icon="mdi-arrow-left"
      @click="goBack"
    >
      Back
    </v-btn>

    <v-card max-width="600px">
      <v-card-title class="text-h5">
        Register
      </v-card-title>

      <v-divider class="my-2" />

      <v-card-text>
        <v-text-field
          v-model="username"
          label="Username"
          variant="outlined"
          @keydown.enter="register"
        />

        <v-text-field
          v-model="password"
          class="mt-4"
          label="Password"
          variant="outlined"
          :type="isShowPassword
            ? 'text'
            : 'password'"
          :append-inner-icon="isShowPassword
            ? 'mdi-eye'
            : 'mdi-eye-off'"
          @click:append-inner="isShowPassword = !isShowPassword"
          @keydown.enter="register"
        />

        <v-btn
          :loading="loading"
          class="mt-4"
          block
          size="large"
          color="primary"
          @click="register"
        >
          Register
        </v-btn>
      </v-card-text>
    </v-card>
  </div>
</template>
