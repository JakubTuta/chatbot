<script setup lang="ts">
import type { IGenerationParams } from '~/stores/chatStore'

const props = defineProps<{
  persona: { id: string, name: string } | null
  params: IGenerationParams
  activeCollectionsCount: number
  toolsEnabled: boolean
  toolsAvailable: boolean
  jsonEnabled: boolean
  jsonFieldCount: number
  hasHistory: boolean
}>()

const emit = defineEmits<{
  (e: 'open', target: 'persona' | 'parameters' | 'files' | 'templates' | 'json'): void
  (e: 'toggleTools'): void
  (e: 'export', format: 'md' | 'json'): void
}>()

const isOpen = defineModel<boolean>({ default: false })

const paramsSummary = computed(() => {
  const count = [props.params.temperature, props.params.top_p, props.params.num_ctx, props.params.seed]
    .filter(v => v !== null)
    .length

  return count
    ? `${count} set`
    : 'default'
})

function pick(target: 'persona' | 'parameters' | 'files' | 'templates' | 'json') {
  emit('open', target)
  isOpen.value = false
}

function pickExport(format: 'md' | 'json') {
  if (!props.hasHistory)
    return
  emit('export', format)
  isOpen.value = false
}
</script>

<template>
  <v-menu
    v-model="isOpen"
    :close-on-content-click="false"
    location="top start"
    transition="dialog-rise-transition"
  >
    <template #activator="{'props': menuProps}">
      <button
        type="button"
        class="plus-btn"
        title="Add to this chat"
        aria-label="Add to this chat"
        v-bind="menuProps"
      >
        <v-icon size="16">
          mdi-plus
        </v-icon>
      </button>
    </template>

    <div class="plus-popover">
      <div class="mono-kicker plus-popover-header">
        Add to this chat
      </div>

      <button
        type="button"
        class="plus-row"
        @click="pick('persona')"
      >
        <span>Persona</span>

        <span
          class="plus-row-value font-mono"
          :class="{'plus-row-value--set': persona}"
        >{{ persona?.name ?? 'default' }}</span>
      </button>

      <button
        type="button"
        class="plus-row"
        @click="pick('files')"
      >
        <span>Files</span>

        <span
          class="plus-row-value font-mono"
          :class="{'plus-row-value--set': activeCollectionsCount}"
        >
          {{ activeCollectionsCount
            ? `${activeCollectionsCount} active`
            : 'none' }}
        </span>
      </button>

      <button
        type="button"
        class="plus-row"
        @click="pick('parameters')"
      >
        <span>Parameters</span>

        <span
          class="plus-row-value font-mono"
          :class="{'plus-row-value--set': paramsSummary !== 'default'}"
        >{{ paramsSummary }}</span>
      </button>

      <button
        type="button"
        class="plus-row"
        @click="pick('templates')"
      >
        <span>Prompt template</span>

        <span class="plus-row-value font-mono">
          use
        </span>
      </button>

      <button
        type="button"
        class="plus-row"
        @click="pick('json')"
      >
        <span>JSON output</span>

        <span
          class="plus-row-value font-mono"
          :class="{'plus-row-value--set': jsonEnabled}"
        >
          {{ jsonEnabled
            ? `${jsonFieldCount} field${jsonFieldCount === 1
              ? ''
              : 's'}`
            : 'off' }}
        </span>
      </button>

      <div
        v-if="toolsAvailable"
        class="plus-row plus-row--toggle"
      >
        <span>Tools</span>

        <v-switch
          :model-value="toolsEnabled"
          density="compact"
          hide-details
          color="mint-btn"
          @update:model-value="emit('toggleTools')"
        />
      </div>

      <v-divider class="my-1" />

      <button
        type="button"
        class="plus-row"
        :disabled="!hasHistory"
        @click="pickExport('md')"
      >
        <span>Export conversation</span>

        <span class="plus-row-value font-mono">md</span>
      </button>

      <button
        type="button"
        class="plus-row"
        :disabled="!hasHistory"
        @click="pickExport('json')"
      >
        <span>Export conversation</span>

        <span class="plus-row-value font-mono">json</span>
      </button>
    </div>
  </v-menu>
</template>

<style scoped>
.plus-btn {
  width: 27px;
  height: 27px;
  border-radius: 20px;
  background: var(--color-card);
  border: 1px dashed var(--color-line-dash);
  color: var(--color-ink-3);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  flex-shrink: 0;
  transition: border-color 0.15s ease, color 0.15s ease;
}

.plus-btn:hover {
  border-color: var(--color-mint-border);
  color: var(--color-mint-deep);
}

.plus-popover {
  width: 280px;
  padding: 10px;
  border-radius: 15px;
  background: var(--color-card);
  border: 1px solid var(--color-line);
  box-shadow: var(--shadow-popover);
}

.plus-popover-header {
  padding: 4px 8px 8px;
}

.plus-row {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 8px;
  border-radius: 9px;
  border: none;
  background: transparent;
  color: var(--color-ink);
  font-family: var(--font-sans);
  font-size: 13px;
  cursor: pointer;
  text-align: left;
}

.plus-row:hover:not(:disabled) {
  background: var(--color-soft);
}

.plus-row:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.plus-row--toggle {
  cursor: default;
}

.plus-row--toggle:hover {
  background: transparent;
}

.plus-row-value {
  font-size: 10.5px;
  color: var(--color-ink-3);
  flex-shrink: 0;
}

.plus-row-value--set {
  color: var(--color-mint-deep);
}
</style>
