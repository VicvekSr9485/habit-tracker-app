# Habit Tracker Application

A comprehensive, full-stack habit tracking application built with FastAPI and React.
The backend exposes a REST API plus a Click CLI; the frontend renders a
dashboard, calendar view and analytics charts on top of that API.

## Technical Documentation

- Backend: [backend/TECHNICAL_DOCUMENTATION](backend/TECHNICAL_DOCUMENTATION.md)
- Frontend: [frontend/TECHNICAL_DOCUMENTATION](frontend/TECHNICAL_DOCUMENTATION.md)

## Features

- **Habit Management** — create, read, update and delete daily or weekly habits.
- **Streak Tracking** — current and longest streaks calculated from completion history.
- **Analytics Dashboard** — completion rates, struggling habits and longest-streak callouts.
- **Calendar View** — at-a-glance visualisation of consistency over time.
- **CLI Companion** — every API capability is mirrored in a Click-based command line.
- **Idempotent Completions** — repeat completions in the same period are deduplicated.
- **Concurrency Safe** — the manager layer serialises mutating calls behind a lock.

## Tech Stack

### Backend
- **Framework:** FastAPI (Python 3.10+)
- **Database:** SQLite (built-in, accessed via `sqlite3`)
- **Validation:** Pydantic V2 (`ConfigDict` only — no deprecated nested `Config`)
- **CLI:** Click + tabulate
- **Testing:** Pytest + pytest-cov (≥80% line coverage gate, currently ~94%)

### Frontend
- **Framework:** React 18
- **Build Tool:** Vite
- **Styling:** Tailwind CSS, PostCSS
- **Routing:** React Router DOM
- **Icons:** Lucide React
- **Charts:** Recharts
- **HTTP Client:** Axios

## Architecture

The codebase is organised in clean concentric layers — each layer depends
only on the layers inside it.

```text
┌────────────────────────────────────────────────────────────────────────┐
│  React frontend (Vite)                                                  │
│  pages / components / hooks / services (axios)                          │
└──────────────────┬──────────────────────────────────────────────────────┘
                   │  HTTP (JSON)
┌──────────────────▼──────────────────────────────────────────────────────┐
│  api/   FastAPI routes + dependency injection                           │
│         (validates with Pydantic, never touches SQL)                    │
└──────────────────┬──────────────────────────────────────────────────────┘
                   │  function calls
┌──────────────────▼──────────────────────────────────────────────────────┐
│  core/  HabitManager — caches habits, serialises writes (RLock)         │
│  cli/   Click commands reuse the same manager                           │
└──────────┬───────────────────────────┬───────────────────────────────────┘
           │                           │
┌──────────▼─────────┐     ┌───────────▼────────────────────────────────┐
│  models/habit.py   │     │  storage/  StorageInterface (ABC)          │
│  Habit + streak    │     │            SQLiteStorage (registers        │
│  arithmetic        │     │            datetime adapter & converter)   │
└────────────────────┘     └────────────────────────────────────────────┘
                                       │
                                  SQLite file
```

Key contracts:

- `models/habit.py` — pure domain object, no I/O. Period bucketing,
  streak counting and "broken" detection live here.
- `storage/interface.py` — abstract base class. Swap SQLite for any
  other backend without touching the manager or routes.
- `core/habit_manager.py` — single point of mutation. Holds a
  threading.RLock so concurrent FastAPI workers cannot race on
  completion dedupe or corrupt the in-memory cache.
- `analytics/analytics.py` — pure functions over `List[Habit]`,
  written in a deliberately functional style (`map`/`filter`/`reduce`).

## Project Structure

```text
habit-tracker-app/
├── backend/                   # FastAPI backend application
│   ├── analytics/             # Pure functional habit analytics
│   ├── api/                   # REST routes + dependency injection
│   ├── cli/                   # Click-based command-line interface
│   ├── core/                  # HabitManager (cache + locking)
│   ├── fixtures/              # Sample data seeder
│   ├── models/                # Habit domain model + Pydantic schemas
│   ├── storage/               # Storage abstraction + SQLite implementation
│   ├── tests/                 # Pytest suite (unit + integration + concurrency)
│   ├── main.py                # FastAPI entry point
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                  # React frontend application
│   ├── src/
│   │   ├── components/        # Reusable UI (cards, forms, charts)
│   │   ├── context/           # React context for state management
│   │   ├── hooks/             # useHabits, useAnalytics
│   │   ├── pages/             # Dashboard, Habits, Calendar, Analytics
│   │   ├── services/          # Axios API client
│   │   └── utils/             # Date and streak helpers
│   ├── package.json
│   └── vite.config.js
└── docker-compose.yml         # Container orchestration
```

## Getting Started

### Prerequisites

Either:

- [Docker](https://www.docker.com/) and Docker Compose (recommended)

or:

- [Python 3.10+](https://www.python.org/)
- [Node.js 18+](https://nodejs.org/) and npm

### Method 1: Docker Compose (recommended)

1. Clone the repository and `cd` into the project root.
2. Start the stack:
   ```bash
   docker-compose up --build
   ```
3. Open the app:
   - Frontend: <http://localhost:3000>
   - Backend API: <http://localhost:8000>
   - Interactive API docs (Swagger): <http://localhost:8000/docs>
   - Alternative docs (ReDoc): <http://localhost:8000/redoc>

The backend automatically seeds five sample habits with 28 days of
synthetic completion data on the first start, so the dashboard is
populated immediately.

### Method 2: Manual setup

#### Backend

```bash
cd backend

# Create and activate a virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS / Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the API
python main.py
# → http://localhost:8000
```

Configuration is read from environment variables (or a local `.env`):

| Variable        | Default                | Description                                         |
| --------------- | ---------------------- | --------------------------------------------------- |
| `DATABASE_URL`  | `sqlite:///habits.db`  | SQLite URL. The `sqlite:///` prefix is stripped.    |

#### Frontend

In a second terminal:

```bash
cd frontend

# Tell Vite where the API lives
echo "VITE_API_URL=http://localhost:8000" > .env

# Install and run
npm install
npm run dev
# → http://localhost:5173
```

## Examples

### REST API

```bash
# Create a habit
curl -X POST http://localhost:8000/api/habits \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Morning Run",
    "description": "20 minutes outdoors",
    "periodicity": "daily"
  }'

# List habits
curl http://localhost:8000/api/habits

# Mark today complete (id 1)
curl -X POST http://localhost:8000/api/habits/1/complete \
  -H "Content-Type: application/json" \
  -d '{}'

# Analytics summary
curl http://localhost:8000/api/analytics/summary

# Habits with <50% completion in the last 14 days
curl "http://localhost:8000/api/analytics/struggling?days=14"
```

### CLI

```bash
cd backend

# Top-level help
python -m cli.controller --help

# Create / list / complete / delete
python -m cli.controller create \
  --name "Read 30 min" --description "Read a book" --periodicity daily
python -m cli.controller list
python -m cli.controller list --periodicity weekly
python -m cli.controller complete 1
python -m cli.controller info 1
python -m cli.controller analyze
python -m cli.controller longest
python -m cli.controller delete 1   # interactive confirmation
```

When running the stack via Docker Compose, prefix the same commands
with `docker compose exec -T backend`:

```bash
docker compose exec -T backend python -m cli.controller --help
docker compose exec -T backend python -m cli.controller list
printf 'y\n' | docker compose exec -T backend python -m cli.controller delete 1
```

## Testing

### Backend

Run the suite from the `backend/` directory:

```bash
cd backend
pytest -q
```

With coverage reporting:

```bash
pytest --cov=. --cov-report=term-missing
```

The suite contains **98 tests** across:

- `tests/test_habit.py` — domain model and streak arithmetic
- `tests/test_storage.py` — SQLite round-trips
- `tests/test_analytics.py` — pure analytics functions
- `tests/test_api.py` — FastAPI integration tests via `TestClient`
- `tests/test_cli.py` — Click command surface
- `tests/test_edge_cases.py` — empty inputs, period boundaries, **multi-threaded completion races**

Line coverage currently sits at **~94%**, comfortably above the 80%
target. Running with `-W error` (warnings-as-errors) also passes,
confirming the Pydantic V2 migration and SQLite datetime adapter fix
are clean.

Run the same suite inside Docker:

```bash
docker compose exec -T backend pytest -q
```

### Frontend

```bash
cd frontend
npm run lint
```

## Notable Implementation Details

- **Pydantic V2 migration.** All schemas use `ConfigDict`; no
  `class Config:` blocks remain. `model_dump()` replaces the
  deprecated `.dict()`.
- **Explicit SQLite datetime adapter.** Python 3.12 deprecated the
  default datetime adapter. `storage/sqlite_storage.py` registers
  ISO-8601 adapter and converter at import time and opens connections
  with `detect_types=PARSE_DECLTYPES`, so timestamps round-trip without
  warnings.
- **Thread-safe completion.** `HabitManager.complete_habit` runs the
  *check + write* sequence under an `RLock`, so even with N FastAPI
  workers racing on the same habit only one row is persisted per period.
- **ISO-week semantics for weekly habits.** Sunday and the following
  Monday belong to different ISO weeks — the test suite pins this
  explicitly so refactors can't silently change it.

## License

This project was produced as coursework for the IU "Object-Oriented and
Functional Programming with Python" module and is provided for
educational purposes.
