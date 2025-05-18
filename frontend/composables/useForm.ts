export default function useForm() {
  const form: Ref<null | {
    resetValidation: () => void
    reset: () => void
    validate: () => Promise<{ valid: boolean }>
  }> = ref(null)

  const valid = ref(false)

  const isValid = async () => {
    try {
      const tmp = (await form.value?.validate())?.valid || false
      valid.value = tmp

      return tmp
    }
    catch {
      valid.value = false

      return false
    }
  }

  return {
    form,
    valid,
    isValid,
  }
}
