# CLAUDE.md

Guidance for working in this repo. Local-only Ollama chatbot: Nuxt 3 (SPA, `ssr: false`) →
Django 5 + DRF → Channels/Daphne (ASGI) → Ollama containers spawned via the mounted Docker socket
→ PostgreSQL 16 + Redis (channel layer). No auth — single user, localhost-only by design.

## Engineering principles

1. **Never guess an API — verify with Context7.** Before writing against Django, DRF, Channels,
   LangChain/`langchain-ollama`, the Docker SDK, Nuxt, Vue, Vuetify, Pinia or pgvector, fetch
   current docs via Context7 (`resolve-library-id` → `query-docs`), even for things that look
   obvious. Where behavior can't be settled from docs, probe it live before shipping.
2. **Delete dead code rather than carry it.**
3. **Group logic by domain, one home per concern** — e.g. `django_app/catalog/` (parser + registry
   client + sync), `django_app/rag/` (extraction + chunking + embeddings + retrieval, kept apart
   from the chat consumer that calls it), `django_app/mcp_integration/` (MCP client),
   `django_app/openai_compat/` (OpenAI-compatible request/response handling), Docker lifecycle vs.
   Ollama HTTP calls vs. progress reporting kept separate, frontend `composables/` for WebSocket
   clients rather than `constants/`.
4. **Build for the roadmap, not just the fix.** Async consumers must support cancellation, the
   catalog carries capability flags (tools/vision/embedding), the Ollama client must be reusable
   for embeddings. Don't hardcode assumptions that block these.
5. **Fail loudly, never silently.** No bare `except: pass`, no swallowed parse errors, no success
   returned on an empty or errored result. Every failure carries a message a non-technical user can
   act on.
6. **Types and tests travel with the code.** Type hints on new Python, no `any` in new TypeScript,
   a test with every fix.
7. **Small, reviewable commits, one concern each**, ordered so the tree is runnable at every step.
8. **This app is for people who are new to local AI.** Every user-facing flow (chat, model install,
   RAG, tools) needs a working empty state, a plain-language error message, and a guard against the
   obvious "something isn't ready yet" case (Docker down, model still pulling, container stopped) —
   never a silent no-op or a raw stack trace.

## Conventions

- WebSocket/API error payloads use lowercase `"error"` / `"status"` keys, consistently.
- Use `logger`, never `print`, in backend code.
- Migrations are **committed** — `migrations/` is not gitignored. Always commit new migration
  files alongside the model change that produced them.
- Component/store naming and structure: see existing `stores/*.ts` (Pinia) and `components/*.vue`
  for the established patterns before adding new ones.
- Destructive or hard-to-reverse user actions (delete chat, delete document, delete MCP server,
  remove a model) always go through `ConfirmDialog.vue` — never a bare click-to-delete button.
- A backend dependency pin that "already works" in a stale local venv can still fail a clean
  `pip install -r requirements.txt` in the Docker image — always verify new/changed pins against a
  fresh `docker compose build`, not just the local environment.

## Commands

```bash
# Backend (django_server/)
python manage.py runserver          # dev server
python manage.py migrate            # apply migrations
pytest                              # tests
ruff check .                        # lint

# Frontend (frontend/)
npm run dev                         # dev server
npm run test                        # vitest
npm run typecheck                   # vue-tsc
npx eslint .                        # lint
npx playwright test                 # e2e (needs the stack running)

# Full stack
docker-compose up -d
```

## Guardrails

- Never reintroduce `AIModel.objects.all().delete()` (or any catalog refresh path that deletes
  before a successful, validated re-scrape) — it cascades into `ChatHistory`/`ChatMessage` and
  destroys user data.
- Never expose this app beyond `127.0.0.1` while `/var/run/docker.sock` is mounted into the
  backend container — that socket is equivalent to host root.
- Never claim a feature in `README.md` that isn't actually in the code.
