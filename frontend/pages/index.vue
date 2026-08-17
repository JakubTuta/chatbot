<script setup lang="ts">
const hardwareStore = useHardwareStore()
const { hardware, diskUsage } = storeToRefs(hardwareStore)

onMounted(() => {
  hardwareStore.fetchDiskUsage()
  hardwareStore.fetchHardware()
})

function formatBytesOrUnknown(bytes: number | null): string {
  return bytes === null
    ? '—'
    : formatBytes(bytes)
}
</script>

<template>
  <AppTopBar />

  <div class="home-page">
    <div class="home-inner">
      <SystemStatusBanner style="margin-top: 16px" />

      <section class="hero">
        <div class="hero-copy">
          <div class="mono-kicker hero-kicker">
            Local only · No account · Your machine
          </div>

          <h1 class="hero-headline">
            A proper chat UI for the models running on your own machine
          </h1>

          <p class="hero-body">
            ReiChat sits on top of Ollama — install models with one click, keep organised
            conversation history, reference your own files, and compare models side by side, all
            without your data ever leaving this computer.
          </p>

          <div class="hero-buttons">
            <v-btn
              to="/chat"
              color="mint-btn"
              variant="flat"
              rounded="lg"
              size="large"
            >
              Get started →
            </v-btn>

            <v-btn
              to="/models"
              variant="outlined"
              rounded="lg"
              size="large"
            >
              Explore models
            </v-btn>
          </div>

          <div class="hero-stats">
            <div class="hero-stat">
              <span class="hero-stat-value">{{ diskUsage.models.length }}</span>

              <span class="mono-kicker">on this machine</span>
            </div>

            <div class="hero-stat">
              <span class="hero-stat-value">{{ formatBytes(diskUsage.total_bytes) }}</span>

              <span class="mono-kicker">disk used by models</span>
            </div>

            <div class="hero-stat">
              <span class="hero-stat-value">{{ formatBytesOrUnknown(hardware.ram_bytes) }} / {{ formatBytesOrUnknown(hardware.vram_bytes) }}</span>

              <span class="mono-kicker">ram / vram detected</span>
            </div>
          </div>
        </div>

        <div class="hero-shot">
          <div class="hero-shot-frame">
            <div class="mock-window-dots">
              <span />

              <span />

              <span />
            </div>

            <div class="mock-row">
              <span class="mock-dot" />

              <div class="mock-lines">
                <span
                  class="mock-line"
                  style="width: 88%"
                />

                <span
                  class="mock-line"
                  style="width: 62%"
                />
              </div>
            </div>

            <div class="mock-trace font-mono">
              <span class="mock-trace-name">get_current_time</span>() → "14:32"
            </div>

            <div class="mock-row mock-row--user">
              <span class="mock-bubble" />
            </div>

            <div class="mock-row">
              <span class="mock-dot" />

              <div class="mock-lines">
                <span
                  class="mock-line"
                  style="width: 74%"
                />
              </div>
            </div>
          </div>

          <div class="hero-shot-caption mono-kicker">
            Product shot — chat with tool trace
          </div>
        </div>
      </section>

      <section class="pieces">
        <div class="piece-box">
          Docker
        </div>

        <span class="piece-arrow font-mono">→</span>

        <div class="piece-box">
          Ollama
        </div>

        <span class="piece-arrow font-mono">→</span>

        <div class="piece-box piece-box--active">
          ReiChat
        </div>
      </section>

      <section class="explainer-grid">
        <div class="panel">
          <div class="mono-kicker panel-kicker">
            What is Ollama?
          </div>

          <h3 class="panel-title">
            The engine underneath
          </h3>

          <p class="panel-body">
            <a
              href="https://ollama.com"
              target="_blank"
              rel="noopener noreferrer"
            >Ollama</a> is a free tool that runs open-source AI language models — Llama, Mistral,
            Gemma, Qwen and more — directly on your CPU or GPU. No account, no API key, no
            per-message cost.
          </p>
        </div>

        <div class="panel">
          <div class="mono-kicker panel-kicker">
            What ReiChat adds
          </div>

          <h3 class="panel-title">
            A proper interface
          </h3>

          <p class="panel-body">
            Ollama by itself is a command-line tool. ReiChat gives it a chat interface: install
            models with one click, keep organised history, reference your own files, and compare
            models side by side.
          </p>
        </div>

        <div class="panel">
          <div class="mono-kicker panel-kicker">
            Why local
          </div>

          <h3 class="panel-title">
            Privacy, with trade-offs
          </h3>

          <p class="panel-body">
            Nothing you type leaves this machine — no cloud, no data collection, works offline once
            a model is downloaded. In exchange, local models are typically smaller and slower than
            the largest cloud ones, and need free disk space and RAM.
          </p>
        </div>
      </section>

      <section class="steps-section">
        <h2 class="section-title">
          Get started in three steps
        </h2>

        <div class="steps-grid">
          <div class="step-card">
            <div class="step-number">
              1
            </div>

            <h3 class="step-title">
              Install &amp; start Docker
            </h3>

            <p class="step-body">
              Download Docker Desktop and start it. ReiChat uses Docker to run each AI model in its
              own isolated container.
            </p>
          </div>

          <div class="step-card">
            <div class="step-number">
              2
            </div>

            <h3 class="step-title">
              Pull a model
            </h3>

            <p class="step-body">
              Pick a model, select a version and click <strong>Create container</strong> — it
              downloads automatically.
            </p>

            <NuxtLink
              to="/models"
              class="step-link"
            >
              Go to Models →
            </NuxtLink>
          </div>

          <div class="step-card">
            <div class="step-number">
              3
            </div>

            <h3 class="step-title">
              Start chatting
            </h3>

            <p class="step-body">
              Once the container shows <strong>Running</strong>, your model is ready and waiting.
            </p>

            <NuxtLink
              to="/chat"
              class="step-link"
            >
              Open Chat →
            </NuxtLink>
          </div>
        </div>
      </section>

      <section class="cta-block">
        <h2 class="cta-headline">
          Ready to start chatting?
        </h2>

        <p class="cta-body">
          Everything runs on this machine — open a chat or browse the model catalogue to get set up.
        </p>

        <div class="cta-buttons">
          <v-btn
            to="/chat"
            variant="flat"
            rounded="lg"
            style="background: oklch(0.32 0.05 168); color: white"
          >
            Open chat
          </v-btn>

          <v-btn
            to="/models"
            variant="outlined"
            rounded="lg"
            style="border-color: oklch(0.5 0.09 168 / .4); color: oklch(0.3 0.06 168)"
          >
            Browse models
          </v-btn>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.home-page {
  min-height: 100vh;
}

.home-inner {
  max-width: 1000px;
  margin: 0 auto;
  padding: 0 20px 60px;
}

.hero {
  display: grid;
  grid-template-columns: 1.05fr 0.95fr;
  gap: 44px;
  padding: 7vh 0 6vh;
  align-items: center;
}

.hero-kicker {
  margin-bottom: 14px;
}

.hero-headline {
  font-size: 46px;
  line-height: 1.1;
  font-weight: 400;
  letter-spacing: -0.03em;
  color: var(--color-ink);
  margin: 0 0 18px;
}

.hero-body {
  font-size: 16px;
  line-height: 1.65;
  color: var(--color-ink-2);
  margin: 0 0 26px;
  max-width: 46ch;
}

.hero-buttons {
  display: flex;
  gap: 12px;
  margin-bottom: 34px;
}

.hero-stats {
  display: flex;
  gap: 34px;
  padding-top: 18px;
  border-top: 1px solid var(--color-line);
  flex-wrap: wrap;
}

.hero-stat {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.hero-stat-value {
  font-size: 20px;
  font-weight: 500;
  color: var(--color-ink);
}

.hero-shot {
  background: var(--color-soft);
  border-radius: 15px;
  padding: 14px;
}

.hero-shot-frame {
  height: 250px;
  border-radius: 10px;
  padding: 18px 20px;
  background: var(--color-card);
  border: 1px solid var(--color-line-2);
  display: flex;
  flex-direction: column;
  gap: 12px;
  overflow: hidden;
}

.mock-window-dots {
  display: flex;
  gap: 5px;
  margin-bottom: 2px;
}

.mock-window-dots span {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--color-line-2);
}

.mock-row {
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.mock-row--user {
  justify-content: flex-end;
}

.mock-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--color-mint);
  margin-top: 5px;
  flex-shrink: 0;
}

.mock-lines {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.mock-line {
  display: block;
  height: 7px;
  border-radius: 4px;
  background: var(--color-soft-2);
}

.mock-trace {
  align-self: flex-start;
  margin-left: 14px;
  padding: 6px 10px;
  border-radius: 8px;
  background: var(--color-soft-2);
  border: 1px solid var(--color-line-2);
  font-size: 10.5px;
  color: var(--color-ink-2);
}

.mock-trace-name {
  color: var(--color-mint-deep);
}

.mock-bubble {
  display: block;
  width: 62%;
  height: 30px;
  border-radius: 12px 12px 3px 12px;
  background: var(--color-mint-tint);
}

.hero-shot-caption {
  text-align: center;
  padding-top: 12px;
}

.pieces {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 14px;
  padding: 10px 0 48px;
}

.piece-box {
  padding: 10px 22px;
  border-radius: 12px;
  border: 1px solid var(--color-line-2);
  background: var(--color-card);
  font-size: 13px;
  font-weight: 500;
  color: var(--color-ink-2);
}

.piece-box--active {
  background: var(--color-mint-tint);
  border-color: var(--color-mint-border);
  color: var(--color-ink);
}

.piece-arrow {
  color: var(--color-ink-3);
  font-size: 13px;
}

.explainer-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 18px;
  padding-bottom: 60px;
}

.panel {
  background: var(--color-soft);
  border-radius: 15px;
  padding: 22px;
}

.panel-kicker {
  margin-bottom: 10px;
}

.panel-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-ink);
  margin: 0 0 8px;
}

.panel-body {
  font-size: 13px;
  line-height: 1.65;
  color: var(--color-ink-2);
  margin: 0;
}

.panel-body a {
  color: var(--color-mint-deep);
}

.section-title {
  font-size: 24px;
  font-weight: 400;
  letter-spacing: -0.02em;
  color: var(--color-ink);
  text-align: center;
  margin: 0 0 30px;
}

.steps-section {
  padding-bottom: 60px;
}

.steps-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 20px;
}

.step-card {
  position: relative;
  background: var(--color-card);
  border: 1px solid var(--color-line-2);
  border-radius: 15px;
  padding: 26px 20px 20px;
}

.step-number {
  position: absolute;
  top: -14px;
  left: 20px;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--color-mint-btn);
  color: var(--color-mint-ink);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 13px;
}

.step-title {
  font-size: 14.5px;
  font-weight: 600;
  color: var(--color-ink);
  margin: 4px 0 8px;
}

.step-body {
  font-size: 13px;
  line-height: 1.6;
  color: var(--color-ink-2);
  margin: 0 0 10px;
}

.step-link {
  font-size: 12.5px;
  font-weight: 500;
  color: var(--color-mint-deep);
  text-decoration: none;
}

.step-link:hover {
  text-decoration: underline;
}

.cta-block {
  background: var(--color-mint-tint);
  border-radius: 20px;
  padding: 30px 34px;
  text-align: center;
}

.cta-headline {
  font-size: 24px;
  font-weight: 400;
  letter-spacing: -0.02em;
  color: var(--color-ink);
  margin: 0 0 8px;
}

.cta-body {
  font-size: 14px;
  color: var(--color-ink-2);
  margin: 0 0 20px;
}

.cta-buttons {
  display: flex;
  justify-content: center;
  gap: 12px;
  flex-wrap: wrap;
}

@media (max-width: 900px) {
  .hero {
    grid-template-columns: 1fr;
  }

  .hero-shot {
    order: -1;
  }
}

@media (max-width: 600px) {
  .hero-headline {
    font-size: 34px;
  }

  .pieces {
    flex-wrap: wrap;
  }
}
</style>
