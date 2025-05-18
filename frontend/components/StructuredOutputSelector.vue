<script setup lang="ts">
const format = defineModel<{
  field: string
  type: string
  description: string
}[]>('format', { default: () => [], required: true })
const isFormValid = defineModel<boolean>('isFormValid', { default: () => false, required: true })

const { form, isValid } = useForm()

const simpleTypes = [
  { value: 'string', title: 'String' },
  { value: 'number', title: 'Number' },
  { value: 'boolean', title: 'Boolean' },
  { value: 'date', title: 'Date' },
]

const possibleTypes = [
  ...simpleTypes,
  // { value: 'array', title: 'Array' },
  // { value: 'object', title: 'Object' },
]

function addNewType() {
  format.value.push({ field: '', type: '' })
}

function removeType(index: number) {
  format.value.splice(index, 1)
}

async function validate() {
  isFormValid.value = await isValid()
}
</script>

<template>
  <v-menu
    activator="parent"
    :close-on-content-click="false"
    @click:outside="validate()"
  >
    <v-card
      width="500px"
    >
      <v-form
        ref="form"
        validate-on="eager"
      >
        <v-card-text>
          <v-row
            v-for="(formatLine, index) in format"
            :key="index"
            class="my-2"
            dense
            align-center
          >
            <v-text-field
              v-model="formatLine.field"
              density="compact"
              :rules="[requiredRule()]"
              class="w-40%"
              label="Field"
            />

            <v-select
              v-model="formatLine.type"
              class="mx-2 w-40%"
              :items="possibleTypes"
              density="compact"
              :rules="[requiredRule()]"
              label="Type"
            />

            <v-btn
              icon="mdi-delete"
              color="error"
              variant="text"
              size="small"
              class="w-10%"
              @click="removeType(index)"
            />

            <v-textarea
              v-model="formatLine.description"
              density="compact"
              class="mt-3 max-w-90%"
              label="Description"
              variant="outlined"
              rows="1"
              auto-grow
              hint="(Optional) Any additional information about the field that may help the model to best understand it."
            />

            <v-divider
              v-if="index < format.length - 1"
              class="mb-4"
            />
          </v-row>

          <div class="mt-4 flex justify-center">
            <v-btn
              append-icon="mdi-plus"
              @click="addNewType"
            >
              Add
            </v-btn>
          </div>
        </v-card-text>
      </v-form>
    </v-card>
  </v-menu>
</template>
