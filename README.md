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

## Running app with docker

#### 1. Clone the repository:

```bash
git clone https://github.com/JakubTuta/chatbot.git

cd chatbot
```

#### 2. Starting app

```bash
docker-compose up -d
```

Django server runs on `http://localhost:8000` \
Nuxt web app runs on `http://localhost:3000` \
MongoDB runs on `http://localhost:27017`

## Running each module separately

### 1. Starting server

```bash
cd django_server
```

Create virtual environment

```bash
python -m venv venv
```

Run virtual environment

```bash
# on Windows
venv/Scripts/activate

# on MacOS / Linux
source venv/bin/activate
```

Install the modules:

```bash
pip install -r requirements.txt
```

Create `.env` file in `backend` directory with following content (check .env.example for reference):

```bash
SECRET_KEY: Django secret key (you can generate it [here](https://djecrety.ir/))
DEBUG: true/false
DATABASE_USERNAME: Database username
DATABASE_PASSWORD: Database password
DATABASE_NAME: Database name
DATABASE_PORT: Database port
MONGO_CONTAINER_NAME: MongoDB container name (for example mongodb)
LOCAL_DATABASE_HOST: MongoDB url (for example hosted on docker) (for communication between local and docker)
DOCKER_DATABASE_HOST: MongoDB url (for example hosted on docker) (for communication between docker and docker)

# Optional
PRODUCTION_DATABASE_HOST: Production MongoDB url (for example hosted on mongodb atlas)
IS_PRODUCTION: true if production, false if local
```

Make sure the mongodb database is running on `http://localhost:27017` \
ONLY FOR THE FIRST TIME:

```bash
python replace_context.py
python manage.py migrate
```

Now you can run server

```bash
python manage.py runserver
```

Django server is running on `http://localhost:8000`

### 2. Starting Nuxt app

```bash
cd frontend
```

Install the dependencies:

```bash
# replace npm with any package manager
npm install
```

```bash
# # replace npm with any package manager
npm run dev
```

Nuxt app is running on `http://localhost:3000`

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.