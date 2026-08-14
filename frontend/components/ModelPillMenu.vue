<script setup lang="ts">
import type { IContainer } from '~/models/container'

defineProps<{
  models: IContainer[]
}>()

const selectedModel = defineModel<IContainer | null>({ default: null })

const isOpen = ref(false)

function selectModel(model: IContainer) {
  selectedModel.value = model
  isOpen.value = false
}
</script>

<template>
  <v-menu
    v-model="isOpen"
    location="bottom end"
    transition="dialog-rise-transition"
  >
    <template #activator="{'props': menuProps}">
      <button
        type="button"
        class="model-pill"
        v-bind="menuProps"
      >
        <span
          class="model-pill-dot"
          :class="{'model-pill-dot--live': selectedModel?.status === 'running'}"
        />

        <span class="model-pill-name">{{ selectedModel?.name ?? 'No model' }}</span>

        <span
          v-if="selectedModel"
          class="model-pill-tag font-mono"
        >{{ selectedModel.parameters }} ▾</span>
      </button>
    </template>

    <div class="model-pill-popover">
      <button
        v-for="model in models"
        :key="`${model.model}-${model.parameters}`"
        type="button"
        class="model-pill-row"
        :class="{'model-pill-row--active': selectedModel?.model === model.model && selectedModel?.parameters === model.parameters}"
        @click="selectModel(model)"
      >
        <span
          class="model-pill-dot"
          :class="{'model-pill-dot--live': model.status === 'running'}"
        />

        <span class="model-pill-row-name">{{ model.name }}</span>

        <span class="model-pill-row-tag font-mono">{{ model.parameters }}</span>
      </button>

      <div
        v-if="!models.length"
        class="model-pill-empty"
      >
        No models running yet.
      </div>

      <v-divider class="my-1" />

      <NuxtLink
        to="/models"
        class="model-pill-link"
      >
        Add more models →
      </NuxtLink>
    </div>
  </v-menu>
</template>

<style scoped>
.model-pill {
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 6px 12px;
  border-radius: 20px;
  background: var(--color-card);
  border: 1px solid var(--color-line);
  cursor: pointer;
  transition: border-color 0.15s ease;
}

.model-pill:hover {
  border-color: var(--color-mint-border);
}

.model-pill-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--color-grey-dot);
  flex-shrink: 0;
}

.model-pill-dot--live {
  background: var(--color-mint);
  animation: pulse 2.6s ease-in-out infinite;
}

.model-pill-name {
  font-size: 12px;
  font-weight: 500;
  color: var(--color-ink);
}

.model-pill-tag {
  font-size: 11px;
  color: var(--color-ink-3);
}

.model-pill-popover {
  width: 250px;
  padding: 8px;
  border-radius: 15px;
  background: var(--color-card);
  border: 1px solid var(--color-line);
  box-shadow: var(--shadow-popover);
}

.model-pill-row {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px;
  border-radius: 9px;
  border: none;
  background: transparent;
  cursor: pointer;
  text-align: left;
}

.model-pill-row:hover {
  background: var(--color-soft);
}

.model-pill-row--active {
  background: var(--color-mint-tint);
}

.model-pill-row-name {
  flex: 1;
  min-width: 0;
  font-size: 12.5px;
  color: var(--color-ink);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.model-pill-row-tag {
  font-size: 10.5px;
  color: var(--color-ink-3);
  flex-shrink: 0;
}

.model-pill-empty {
  padding: 10px 8px;
  font-size: 12px;
  color: var(--color-ink-2);
}

.model-pill-link {
  display: block;
  padding: 8px;
  font-size: 12.5px;
  color: var(--color-mint-deep);
  text-decoration: none;
}

.model-pill-link:hover {
  text-decoration: underline;
}
</style>
