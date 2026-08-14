<script setup lang="ts">
import type { MCPTransport } from '~/models/mcpServer'

const mcpServerStore = useMCPServerStore()
const { servers, loading } = storeToRefs(mcpServerStore)

const deleteConfirmDialog = ref(false)
const serverToDelete = ref<{ id: number, name: string } | null>(null)

const creating = ref(false)
const newName = ref('')
const newTransport = ref<MCPTransport>('stdio')
const newCommandOrUrl = ref('')
const saving = ref(false)

onMounted(() => {
  mcpServerStore.fetchServers()
})

function openCreateForm() {
  creating.value = true
  newName.value = ''
  newTransport.value = 'stdio'
  newCommandOrUrl.value = ''
}

function cancelCreate() {
  creating.value = false
}

async function submitCreate() {
  const name = newName.value.trim()
  const commandOrUrl = newCommandOrUrl.value.trim()
  if (!name || !commandOrUrl)
    return

  saving.value = true
  const succeeded = await mcpServerStore.createServer(name, newTransport.value, commandOrUrl)
  saving.value = false

  if (succeeded)
    creating.value = false
}

async function toggleEnabled(server: { id: number, enabled: boolean }) {
  await mcpServerStore.setServerEnabled(server.id, !server.enabled)
}

function requestDelete(server: { id: number, name: string }) {
  serverToDelete.value = server
  deleteConfirmDialog.value = true
}

async function confirmDelete() {
  deleteConfirmDialog.value = false
  if (!serverToDelete.value)
    return

  await mcpServerStore.deleteServer(serverToDelete.value.id)
  serverToDelete.value = null
}

function cancelDelete() {
  deleteConfirmDialog.value = false
  serverToDelete.value = null
}
</script>

<template>
  <AppTopBar />

  <div class="integrations-page">
    <h1 class="page-h1">
      Integrations
    </h1>

    <p class="page-lede">
      MCP servers you connect here contribute their tools to any chat with <strong>Tools</strong>
      turned on — alongside the built-in calculator and current-time tools.
    </p>

    <div
      v-if="!servers.length && !loading && !creating"
      class="empty-card"
    >
      No MCP servers configured yet.
    </div>

    <div
      v-if="servers.length"
      class="server-list"
    >
      <div
        v-for="server in servers"
        :key="server.id"
        class="server-row"
      >
        <v-switch
          :model-value="server.enabled"
          density="compact"
          hide-details
          color="mint-btn"
          :title="server.enabled
            ? 'Disable'
            : 'Enable'"
          :aria-label="server.enabled
            ? `Disable ${server.name}`
            : `Enable ${server.name}`"
          @update:model-value="toggleEnabled(server)"
        />

        <div class="server-main">
          <span class="server-name">{{ server.name }}</span>

          <span class="server-command font-mono">
            {{ server.transport === 'stdio'
              ? server.command
              : server.url }}
          </span>
        </div>

        <span class="badge badge--grey">{{ server.transport === 'stdio'
          ? 'STDIO'
          : 'HTTP' }}</span>

        <button
          type="button"
          class="server-delete"
          title="Delete MCP server"
          aria-label="Delete MCP server"
          @click="requestDelete(server)"
        >
          Delete
        </button>
      </div>
    </div>

    <template v-if="creating">
      <div class="add-form">
        <v-text-field
          v-model="newName"
          label="Server name"
          density="compact"
          autofocus
          class="mb-2"
        />

        <div class="transport-pills">
          <button
            type="button"
            class="transport-pill"
            :class="{'transport-pill--active': newTransport === 'stdio'}"
            @click="newTransport = 'stdio'"
          >
            Local command
          </button>

          <button
            type="button"
            class="transport-pill"
            :class="{'transport-pill--active': newTransport === 'http'}"
            @click="newTransport = 'http'"
          >
            HTTP streamable
          </button>
        </div>

        <v-text-field
          v-model="newCommandOrUrl"
          :label="newTransport === 'stdio'
            ? 'Command (e.g. `python server.py`)'
            : 'URL (e.g. http://localhost:9000/mcp)'"
          density="compact"
          hide-details
          class="mb-3"
        />

        <div class="add-form-actions">
          <v-btn
            variant="text"
            @click="cancelCreate"
          >
            Cancel
          </v-btn>

          <v-btn
            color="mint-btn"
            variant="flat"
            :loading="saving"
            :disabled="!newName.trim() || !newCommandOrUrl.trim()"
            @click="submitCreate"
          >
            Add server
          </v-btn>
        </div>
      </div>
    </template>

    <button
      v-else
      type="button"
      class="dashed-add-row"
      @click="openCreateForm"
    >
      + Add a server
    </button>
  </div>

  <ConfirmDialog
    v-model="deleteConfirmDialog"
    title="Delete MCP server"
    message="Chats with Tools on will no longer be able to call this server's tools. This can't be undone."
    confirm-label="Delete"
    confirm-color="red"
    @confirm="confirmDelete"
    @cancel="cancelDelete"
  />
</template>

<style scoped>
.integrations-page {
  max-width: 760px;
  margin: 0 auto;
  padding: 28px 20px 60px;
}

.page-h1 {
  font-size: 30px;
  font-weight: 400;
  letter-spacing: -0.025em;
  color: var(--color-ink);
  margin: 0 0 6px;
}

.page-lede {
  font-size: 14px;
  line-height: 1.6;
  color: var(--color-ink-2);
  margin: 0 0 22px;
}

.empty-card {
  padding: 30px;
  text-align: center;
  font-size: 13px;
  color: var(--color-ink-2);
  background: var(--color-card);
  border: 1px solid var(--color-line-2);
  border-radius: 13px;
  margin-bottom: 14px;
}

.server-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 14px;
}

.server-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  background: var(--color-card);
  border: 1px solid var(--color-line-2);
  border-radius: 13px;
}

.server-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.server-name {
  font-size: 13.5px;
  font-weight: 500;
  color: var(--color-ink);
}

.server-command {
  font-size: 10.5px;
  color: var(--color-ink-3);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.badge {
  font-family: var(--font-mono);
  font-size: 9.5px;
  padding: 2px 6px;
  border-radius: 5px;
  flex-shrink: 0;
}

.badge--grey {
  background: var(--color-soft-2);
  color: var(--color-ink-2);
}

.server-delete {
  flex-shrink: 0;
  border: none;
  background: transparent;
  color: var(--color-ink-3);
  font-size: 11.5px;
  cursor: pointer;
}

.server-delete:hover {
  color: var(--color-red);
}

.add-form {
  background: var(--color-card);
  border: 1px solid var(--color-line-2);
  border-radius: 13px;
  padding: 16px;
}

.transport-pills {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.transport-pill {
  flex: 1;
  padding: 8px 12px;
  border-radius: 10px;
  border: 1px solid var(--color-line);
  background: var(--color-soft);
  color: var(--color-ink-2);
  font-family: var(--font-sans);
  font-size: 12.5px;
  cursor: pointer;
}

.transport-pill--active {
  background: var(--color-mint-tint);
  border-color: var(--color-mint-border);
  color: oklch(0.4 0.07 168);
}

.add-form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
</style>
