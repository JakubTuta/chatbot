<template>
  <div
    class="assistant-message"
    role="status"
    aria-label="Assistant is typing"
  >
    <div class="assistant-header">
      <span class="assistant-dot assistant-dot--live" />
    </div>

    <div
      class="typing-dots"
      aria-hidden="true"
    >
      <span />

      <span />

      <span />
    </div>
  </div>
</template>

<style scoped>
.assistant-message {
  width: 100%;
}

.assistant-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.assistant-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: var(--color-mint);
}

.assistant-dot--live {
  animation: pulse 1.6s ease-in-out infinite;
}

.typing-dots {
  display: flex;
  align-items: center;
  gap: 5px;
  height: 16px;
  padding-left: 1px;
}

.typing-dots span {
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background-color: var(--color-ink-3);
  animation: dots 1.2s infinite;
}

.typing-dots span:nth-child(1) { animation-delay: 0s; }
.typing-dots span:nth-child(2) { animation-delay: 0.2s; }
.typing-dots span:nth-child(3) { animation-delay: 0.4s; }
</style>
