# Chatbot

## Overview

**Chatbot** is a self-hosted web app for running and chatting with Large Language Models (LLMs) locally using Docker and Ollama. No cloud required — your data stays on your machine.

---

## Features

- **Local LLM execution** — run models via Ollama in Docker containers
- **Real-time chat** — streaming responses over WebSocket
- **Model management** — browse, pull, and run models from the Ollama library
- **Multi-user support** — JWT authentication with per-user chat history
- **Image input** — send images to vision-capable models
- **Structured output** — have models respond in a defined JSON schema
- **Docker management** — start, stop, and remove containers directly from the UI

---

## Screenshots

![Landing page](screenshots/1.png)

![Model management](screenshots/2.png)

![Chat interface](screenshots/3.png)

---

## Quick Start (Docker — recommended)

### Prerequisites

- [Docker](https://www.docker.com/) installed and running

### 1. Clone the repository

```bash
git clone https://github.com/JakubTuta/chatbot.git
cd chatbot
```

### 2. Create the backend environment file

```bash
cp django_server/.env.example django_server/.env
```

The defaults in `.env.example` work out of the box for a local Docker setup. You only need to change `SECRET_KEY` for any serious use.

### 3. Start the app

```bash
docker-compose up -d
```

| Service  | URL                      |
|----------|--------------------------|
| Frontend | http://localhost:3000    |
| Backend  | http://localhost:8000    |
| MongoDB  | localhost:27017          |

### GPU support (optional, increases model performance)

- **Windows** — [NVIDIA GPUs with WSL2](https://docs.docker.com/desktop/features/gpu/)
- **Linux / macOS** — [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html#installation)

---

## Running locally (without Docker)

### Backend

```bash
cd django_server

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # macOS / Linux
# venv\Scripts\activate         # Windows

pip install -r requirements.txt
```

Copy and configure the environment file:

```bash
cp .env.example .env
```

Edit `.env` — the only values you must set for local development:

```env
SECRET_KEY="your-secret-key"        # generate at https://djecrety.ir/
DEBUG="true"
SERVER_URL="http://localhost:8000"
DATABASE_USERNAME="admin"
DATABASE_PASSWORD="password"
DATABASE_NAME="chatbot"
DATABASE_PORT="27017"
MONGO_CONTAINER_NAME="mongodb"
LOCAL_DATABASE_HOST="mongodb://admin:password@localhost:27017/?retryWrites=true&w=majority&appName=chatbot"
DOCKER_DATABASE_HOST="mongodb://admin:password@mongodb/?retryWrites=true&w=majority&appName=chatbot"
```

First-time setup (run once):

```bash
python replace_context.py
python manage.py migrate
```

Start the server:

```bash
python manage.py runserver
```

Backend is available at `http://localhost:8000`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend is available at `http://localhost:3000`.

---

## Environment variables reference

| Variable                  | Required | Default       | Description                                              |
|---------------------------|----------|---------------|----------------------------------------------------------|
| `SECRET_KEY`              | Yes      | —             | Django secret key. Generate at https://djecrety.ir/     |
| `DEBUG`                   | No       | `false`       | Set to `true` for local development                      |
| `SERVER_URL`              | No       | `http://localhost:8000` | Base URL of the backend (used during model scraping) |
| `DATABASE_USERNAME`       | Yes      | —             | MongoDB username                                         |
| `DATABASE_PASSWORD`       | Yes      | —             | MongoDB password                                         |
| `DATABASE_NAME`           | Yes      | —             | MongoDB database name                                    |
| `DATABASE_PORT`           | Yes      | `27017`       | MongoDB port                                             |
| `MONGO_CONTAINER_NAME`    | No       | `mongodb`     | MongoDB container hostname (Docker networking)           |
| `LOCAL_DATABASE_HOST`     | No*      | —             | MongoDB connection string for local development          |
| `DOCKER_DATABASE_HOST`    | No*      | —             | MongoDB connection string when running inside Docker     |
| `PRODUCTION_DATABASE_HOST`| No       | —             | MongoDB Atlas or remote connection string                |
| `IS_PRODUCTION`           | No       | `false`       | Set to `true` to use `PRODUCTION_DATABASE_HOST`          |
| `ALLOWED_HOSTS`           | No       | `*`           | Comma-separated list of allowed host headers             |
| `CORS_ALLOW_ALL_ORIGINS`  | No       | `true`        | Set to `false` and configure `CORS_ALLOWED_ORIGINS` for production |

*At least one of `LOCAL_DATABASE_HOST` or `DOCKER_DATABASE_HOST` is required depending on your setup.

---

## License

MIT — see [LICENSE](LICENSE) for details.
