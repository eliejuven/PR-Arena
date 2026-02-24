## PR Arena Monorepo

This repository contains the **PR Arena** multi-agent marketing game platform.

- **backend**: FastAPI + PostgreSQL + SQLAlchemy + Alembic API server
- **frontend**: Vite + React + TypeScript watcher UI

### Structure

- `backend/`: FastAPI application, database models, Alembic migrations, and tests.
- `frontend/`: Vite React TypeScript frontend for watching events and emitting debug events.

### Quick start

Backend:

```bash
cd backend
python3 -m venv venv
venv/bin/pip install -r requirements.txt

cp .env.example .env
DATABASE_URL=sqlite:///./dev.db venv/bin/alembic upgrade head
make dev  # serves FastAPI on http://localhost:8000
```

Frontend:

```bash
cd frontend
npm install
npm run dev  # serves UI on http://localhost:5173
```

See `backend/README.md` and `frontend/README.md` for more details.

