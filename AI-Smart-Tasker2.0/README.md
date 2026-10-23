<div align="center">

# AI Smart Tasker

**A full-stack task manager that combines deadline tracking, productivity analytics, and optional AI assistance.**

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-14-black?logo=next.js)](https://nextjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.6-3178C6?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-3.4-38B2AC?logo=tailwindcss&logoColor=white)](https://tailwindcss.com/)

**Created and primarily developed by Tanish Chaurasia.**

</div>

---

## Overview

AI Smart Tasker is a portfolio full-stack application for organising tasks and seeing how work gets done. Users can create and update tasks with deadlines, view completion and deadline analytics, generate summaries, and receive AI-assisted task categorisation and deadline nudges. The AI features are optional; task categorisation has a local heuristic fallback.

The frontend is a Next.js App Router application. It communicates with a REST API built with FastAPI, which uses SQLAlchemy for persistence and an OpenAI-compatible API for optional language-model features.

> **Project status:** This repository is an actively evolving portfolio project. It does not currently implement authentication or multi-user access. Do not expose a deployment to untrusted users or use it for sensitive data without adding and validating appropriate access controls.

## Features

- Create, view, update, and delete tasks with due dates, completion state, categories, and priority.
- View task completion, deadline adherence, and productivity analytics.
- Generate and edit summaries with a configurable language model.
- Optionally categorise task descriptions with Gemini; use a local heuristic when the key is not configured.
- Receive generated or fallback deadline messages for overdue work.
- Explore and try the backend endpoints through the automatically generated OpenAPI interface.

## Architecture

```text
┌─────────────────────────────┐       JSON / REST       ┌───────────────────────────┐
│ Next.js + React + TypeScript│ ──────────────────────> │ FastAPI application       │
│ App Router, Tailwind, charts│ <────────────────────── │ Routes, schemas, services │
└─────────────────────────────┘                         └────────────┬──────────────┘
                                                                    │
                                             ┌──────────────────────┴──────────────────────┐
                                             │                                             │
                                     ┌───────▼────────┐                         ┌─────────▼─────────┐
                                     │ SQLAlchemy DB  │                         │ Optional LLM API  │
                                     │ PostgreSQL      │                         │ OpenAI-compatible  │
                                     └────────────────┘                         └───────────────────┘
```

### Repository layout

```text
backend/
  app/
    endpoint/       FastAPI route modules
    models/         SQLAlchemy models
    schemas/        Pydantic request and response schemas
    utils/          Database, LLM, task, summary, and analytics logic
    dependencies.py Application configuration and dependency injection
    main.py         FastAPI app and lifecycle
  config/           Hydra YAML configuration and safe example templates
  scripts/          Database and sample-data helpers
  test/             Backend pytest suite
frontend/
  src/app/          Next.js pages and layouts
  src/components/   Reusable React components
  src/lib/          Frontend API client and utilities
  src/types/        Shared TypeScript types
.github/
  workflows/        CI checks
  ISSUE_TEMPLATE/   Bug and feature request templates
```

## Technology

| Area | Technologies |
|---|---|
| Frontend | Next.js 14, React 18, TypeScript, Tailwind CSS, Recharts |
| Backend | Python 3.11+, FastAPI, Pydantic, SQLAlchemy |
| Configuration | Hydra, OmegaConf, environment variables |
| AI integration | LangChain, OpenAI-compatible chat APIs, optional Gemini categorisation |
| Database | PostgreSQL; SQLite is used by the test suite |
| Quality | pytest, Black, Pylint, ESLint, TypeScript |

## Quick start

### Prerequisites

- Python 3.11 or later
- Node.js 18 or later and npm
- PostgreSQL for a local application database
- Optional: a running OpenAI-compatible model endpoint, or a Gemini API key for categorisation

### 1. Clone and configure

```bash
git clone https://github.com/<YOUR_GITHUB_USERNAME>/AI-Smart-Tasker.git
cd AI-Smart-Tasker
```

Copy the environment and backend configuration examples:

**Windows PowerShell**

```powershell
Copy-Item .env.example .env
Copy-Item backend/config/db/database.yaml.example backend/config/db/database.yaml
Copy-Item backend/config/llm/model_config.yaml.example backend/config/llm/model_config.yaml
```

**macOS / Linux**

```bash
cp .env.example .env
cp backend/config/db/database.yaml.example backend/config/db/database.yaml
cp backend/config/llm/model_config.yaml.example backend/config/llm/model_config.yaml
```

Edit `.env` with your local PostgreSQL credentials and, if needed, your model endpoint and credentials. The `.env` file and the copied YAML files are ignored by Git. The checked-in examples contain placeholders only.

Create a PostgreSQL database and user if you do not already have them:

```sql
CREATE DATABASE taskmanager;
CREATE USER taskmanager_user WITH PASSWORD 'change-this-password';
GRANT ALL PRIVILEGES ON DATABASE taskmanager TO taskmanager_user;
```

The default configuration expects PostgreSQL on `localhost:5432`. If PostgreSQL initialization fails, the development fallback uses the SQLite URL from `SQLITE_DATABASE_URL` (in-memory by default). Configure PostgreSQL for dependable local use.

### 2. Start the backend

From the repository root:

```powershell
# Windows PowerShell
python -m venv backend/venv
.\backend\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m backend.app.main
```

On macOS or Linux, activate with:

```bash
source backend/venv/bin/activate
pip install -r requirements.txt
python -m backend.app.main
```

The API is available at `http://localhost:8000`. Interactive API documentation is at [`/docs`](http://localhost:8000/docs), with ReDoc at `/redoc`.

### 3. Start the frontend

In a second terminal:

```powershell
cd frontend
Copy-Item .env.example .env.local
npm ci
npm run dev
```

On macOS or Linux, replace `Copy-Item` with `cp .env.example .env.local`.

Open `http://localhost:3000`. Set `NEXT_PUBLIC_API_BASE_URL` in `frontend/.env.local` if the backend is running at a different URL. This variable is exposed to the browser; never put secrets in `NEXT_PUBLIC_*` variables.

## Configuration

Backend values are read from the repository-root `.env` file and can also be supplied directly as process environment variables. Process environment values take precedence over `.env`.

| Variable | Default | Purpose |
|---|---|---|
| `APP_ENV` | `development` | Enables the development reload mode when running the module directly |
| `BIND_HOST` | `127.0.0.1` | Backend bind address |
| `BIND_PORT` | `8000` | Backend port |
| `CORS_ORIGINS` | `http://localhost:3000` | Comma-separated allowed browser origins |
| `DB_HOST` | `localhost` | PostgreSQL host |
| `DB_PORT` | `5432` | PostgreSQL port |
| `DB_NAME` | `taskmanager` | Database name |
| `DB_USER` | `taskmanager_user` | Database username |
| `DB_PASSWORD` | `CHANGE_ME` | Database password; replace before connecting to PostgreSQL |
| `SQLITE_DATABASE_URL` | `sqlite:///:memory:` | SQLite fallback URL used if PostgreSQL cannot be initialized |
| `LLM_MODEL_NAME` | `Qwen/Qwen3-VL-4B-Instruct` | Model identifier |
| `LLM_API_BASE` | `http://localhost:8001/v1` | OpenAI-compatible API base URL |
| `LLM_API_KEY` | `EMPTY` | LLM API key; `EMPTY` works for local endpoints that do not require authentication |
| `GEMINI_API_KEY` | unset | Optional key for Gemini task categorisation |

The frontend variable `NEXT_PUBLIC_API_BASE_URL` defaults to `http://localhost:8000/api`; see [`frontend/.env.example`](frontend/.env.example).

## API overview

All application routes are prefixed with `/api`. Request schemas and response models are documented in Swagger UI at `/docs`.

| Area | Methods and endpoints | Purpose |
|---|---|---|
| Tasks | `GET/POST /api/tasks`, `GET/PUT/DELETE /api/tasks/{id}` | Manage tasks |
| Summaries | `POST /api/summaries/generate`, `POST /api/summaries/modify`, `POST /api/summaries/regenerate/{id}` | Generate and edit task summaries |
| Deadlines | `GET /api/deadlines/check`, `GET /api/deadlines/overdue`, `POST /api/deadlines/regenerate-insult/{id}` | Check overdue tasks and create deadline messages |
| Analytics | `GET /api/analytics`, `/api/analytics/completion-stats`, `/api/analytics/deadline-adherence`, `/api/analytics/productivity-trends` | Retrieve productivity metrics |
| Health | `GET /health` | Check backend availability |

## Tests and quality checks

Run the backend test suite from the repository root:

```bash
python -m pytest
python -m black --check backend/app
python -m pylint backend/app --fail-under=7.0
```

Run the frontend checks from `frontend/`:

```bash
npm run lint
npx tsc --noEmit
npm run build
```

The GitHub Actions workflow runs backend tests, formatting and lint checks, and frontend lint, type-check, and production-build checks on pushes and pull requests.

## Contributing

Contributions are welcome. Please open an issue for larger changes, add or update tests, and describe user-facing changes in your pull request. The repository includes [bug](.github/ISSUE_TEMPLATE/bug_report.md), [feature request](.github/ISSUE_TEMPLATE/feature_request.md), and [pull request](.github/PULL_REQUEST_TEMPLATE.md) templates.

Use short [Conventional Commit](https://www.conventionalcommits.org/) messages where practical, for example:

```text
feat: add task filtering by priority
fix: handle empty analytics response
docs: clarify local database setup
```

Before opening a pull request, run the backend and frontend checks listed above. Never include local environment files, database credentials, API keys, logs, or generated build output.

## Author and credits

**Tanish Chaurasia** is the creator and primary developer of AI Smart Tasker.

## License

No license has been selected for this repository yet. Until a license file is added, the code is not granted an open-source reuse license. Choose a license and add its official text before describing the project as open source.
