<script setup lang="ts">
const authStore = useAuthStore()

onMounted(() => {
  authStore.logOut()
})
</script>
