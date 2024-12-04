# Chatbot

## 🚀 Overview
**Chatbot** is a simple yet powerful tool that allows you to pull and run Large Language Models (LLMs) locally using Docker and Ollama. Designed for developers and enthusiasts, this app makes it easy to chat with advanced AI models directly on your device, ensuring privacy and flexibility.

---

## 🌟 Features
- **Local Deployment**: Run AI models securely on your own machine—no cloud required.
- **Docker Support**: Leverage Docker for hassle-free setup and compatibility.
- **Interactive AI Chat**: Engage with Large Language Models in real-time conversations.
- **Privacy First**: Your data stays local, giving you complete control.
- **User friendly UI**: Simple and user friendly front-end app created with Nuxt

---

## 🛠️ Getting Started

### Prerequisites
- [Docker](https://www.docker.com/) installed on your machine

### Enabling models to use NVIDIA GPU (increased performance) [optional]
- Windows [NVIDIA GPUs with WSL2](https://docs.docker.com/desktop/features/gpu/)
- Linux / MacOS [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html#installation)

### Installation
#### 1. Clone the repository:
```bash
git clone https://github.com/your-username/chatbot.git

cd chatbot
```

#### 2. Starting django server
```bash
cd django_server

docker-compose up -d
```

Django server is running on `http://localhost:8000`

#### 3. Starting Nuxt app
```bash
cd frontend
```

Install the dependencies:

```bash
# npm
npm install

# pnpm
pnpm install

# yarn
yarn install

# bun
bun install
```

Start the development server on `http://localhost:3000`:

```bash
# npm
npm run dev

# pnpm
pnpm run dev

# yarn
yarn dev

# bun
bun run dev
```