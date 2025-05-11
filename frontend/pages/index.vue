<template>
  <div class="landing-page">
    <!-- Hero Section with Background Gradient -->
    <div class="hero-section">
      <div class="hero-content">
        <h1 class="main-title">
          Welcome to <span class="highlight">OllamaChat</span>
        </h1>

        <p class="subtitle">
          Your gateway to local AI conversations
        </p>

        <div class="action-buttons">
          <NuxtLink to="/auth/login">
            <v-btn
              color="primary"
              size="large"
              class="get-started-btn"
              elevation="2"
            >
              Get Started
            </v-btn>
          </NuxtLink>

          <NuxtLink to="/models">
            <v-btn
              variant="outlined"
              color="primary"
              size="large"
              class="explore-btn"
            >
              Explore Models
            </v-btn>
          </NuxtLink>
        </div>
      </div>

      <!-- Decorative AI chat bubble illustration -->
      <div class="hero-illustration">
        <div class="chat-bubble user-bubble">
          That's amazing!
        </div>

        <div class="chat-bubble ai-bubble mt-7">
          I run locally on your machine!
        </div>

        <div class="chat-bubble user-bubble">
          How does this work?
        </div>
      </div>
    </div>

    <!-- Features Section -->
    <div class="features-section">
      <h2 class="section-title">
        Why Choose OllamaChat?
      </h2>

      <div class="features-grid">
        <div class="feature-card">
          <div class="feature-icon">
            <v-icon
              size="36"
              color="primary"
            >
              mdi-security
            </v-icon>
          </div>

          <h3>Privacy First</h3>

          <p>All conversations stay on your device. No data sent to external services.</p>
        </div>

        <div class="feature-card">
          <div class="feature-icon">
            <v-icon
              size="36"
              color="primary"
            >
              mdi-docker
            </v-icon>
          </div>

          <h3>Simple Management</h3>

          <p>Effortlessly manage Docker containers hosting your AI models.</p>
        </div>

        <div class="feature-card">
          <div class="feature-icon">
            <v-icon
              size="36"
              color="primary"
            >
              mdi-robot
            </v-icon>
          </div>

          <h3>Multiple Models</h3>

          <p>Switch between different AI models based on your specific needs.</p>
        </div>
      </div>
    </div>

    <!-- Call to Action Section -->
    <div class="cta-section">
      <div class="cta-content">
        <h2>Ready to start chatting?</h2>

        <p>Join our community and explore the power of local AI conversations.</p>

        <div class="cta-buttons">
          <NuxtLink to="/auth/login">
            <v-btn
              color="primary"
              class="mx-2"
            >
              Login
            </v-btn>
          </NuxtLink>

          <NuxtLink to="/auth/register">
            <v-btn
              color="secondary"
              class="mx-2"
            >
              Register
            </v-btn>
          </NuxtLink>

          <NuxtLink to="/chat">
            <v-btn
              variant="tonal"
              color="primary"
              class="mx-2"
            >
              Try Chat
            </v-btn>
          </NuxtLink>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.landing-page {
  min-height: 100vh;
  font-family: 'Inter', sans-serif;
  color: #e0e0e0;
  background-color: #121212;
}

/* Hero Section */
.hero-section {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 4rem 8%;
  background: linear-gradient(135deg, #1a1f35 0%, #0d1425 100%);
  border-radius: 0 0 50px 50px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
}

.hero-content {
  max-width: 600px;
}

.main-title {
  font-size: 3.5rem;
  font-weight: 700;
  margin-bottom: 1rem;
  background: linear-gradient(90deg, #4f8cff, #6b66ff);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  line-height: 1.2;
}

.highlight {
  color: #6b66ff;
}

.subtitle {
  font-size: 1.5rem;
  color: #a0aec0;
  margin-bottom: 2rem;
}

.action-buttons {
  display: flex;
  gap: 1rem;
  margin-top: 2rem;
}

.get-started-btn {
  padding: 0 2rem !important;
}

.explore-btn {
  padding: 0 2rem !important;
}

/* Hero Illustration */
.hero-illustration {
  position: relative;
  width: 320px;
  height: 280px;
}

.chat-bubble {
  position: absolute;
  padding: 1rem 1.5rem;
  border-radius: 18px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
  max-width: 200px;
  animation: float 6s ease-in-out infinite;
}

.user-bubble {
  background-color: #2a3142;
  color: #a9c2ff;
  bottom: 20px;
  left: 0;
  animation-delay: 0.5s;
}

.user-bubble:nth-child(3) {
  bottom: 180px;
  left: 40px;
  animation-delay: 1.5s;
}

.ai-bubble {
  background-color: #4f46e5;
  color: white;
  top: 80px;
  right: 0;
  animation-delay: 1s;
}

@keyframes float {
  0% { transform: translateY(0px); }
  50% { transform: translateY(-10px); }
  100% { transform: translateY(0px); }
}

/* Features Section */
.features-section {
  padding: 5rem 8%;
  text-align: center;
}

.section-title {
  font-size: 2.2rem;
  margin-bottom: 3rem;
  color: #e0e0e0;
}

.features-grid {
  display: flex;
  justify-content: center;
  gap: 2rem;
  flex-wrap: wrap;
}

.feature-card {
  background: #1e1e1e;
  padding: 2rem;
  border-radius: 16px;
  width: 300px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.feature-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 20px rgba(0, 0, 0, 0.3);
}

.feature-icon {
  display: flex;
  justify-content: center;
  margin-bottom: 1.5rem;
}

.feature-card h3 {
  font-size: 1.3rem;
  margin-bottom: 1rem;
  color: #e0e0e0;
}

.feature-card p {
  color: #b0b0b0;
  line-height: 1.6;
}

/* CTA Section */
.cta-section {
  background: linear-gradient(135deg, #2563eb 0%, #4f46e5 100%);
  color: white;
  padding: 4rem 8%;
  text-align: center;
  border-radius: 50px 50px 0 0;
  margin-top: 2rem;
}

.cta-content h2 {
  font-size: 2.2rem;
  margin-bottom: 1rem;
}

.cta-content p {
  font-size: 1.1rem;
  margin-bottom: 2rem;
  opacity: 0.9;
}

.cta-buttons {
  display: flex;
  justify-content: center;
  gap: 1rem;
  flex-wrap: wrap;
}

.cta-buttons .v-btn {
  color: white !important;
  font-weight: 600;
  letter-spacing: 0.5px;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
}

/* Responsive Design */
@media (max-width: 1024px) {
  .hero-section {
    flex-direction: column;
    padding: 3rem 5%;
    text-align: center;
  }

  .hero-content {
    max-width: 100%;
    margin-bottom: 3rem;
  }

  .action-buttons {
    justify-content: center;
  }

  .hero-illustration {
    width: 280px;
  }
}

@media (max-width: 768px) {
  .main-title {
    font-size: 2.5rem;
  }

  .subtitle {
    font-size: 1.2rem;
  }

  .features-grid {
    flex-direction: column;
    align-items: center;
  }

  .cta-section {
    padding: 3rem 5%;
  }
}
</style>
