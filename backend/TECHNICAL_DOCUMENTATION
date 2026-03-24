# Backend Technical Documentation

## 1. Overview

The backend is a FastAPI service that manages habits, records completions, computes streaks, and exposes analytics endpoints.

Primary responsibilities:
- Domain modeling for habits and streak logic.
- Persistence using SQLite.
- REST API for CRUD, completion tracking, and analytics.
- Optional CLI workflow for local operations.
- Test coverage for core model logic, storage, and analytics.

## 2. Runtime Architecture

Request flow:
1. Incoming HTTP request hits FastAPI in main.py.
2. Route handler in api/routes.py validates input with Pydantic models.
3. Route uses dependency-injected HabitManager from api/dependencies.py.
4. HabitManager coordinates operations with a storage adapter.
5. SQLiteStorage persists and loads data from habits.db.
6. Response model serializes computed streak and metadata back to client.

Lifecycle behavior:
- On startup, lifespan checks whether habits exist.
- If database is empty, fixture loader seeds sample data.
- On shutdown, shared storage connection is closed.

## 3. Module-by-Module Breakdown

### 3.1 main.py
- Creates FastAPI app with title/version metadata.
- Registers CORS for local frontend origins (3000 and 5173 host variants).
- Mounts API router.
- Provides:
  - GET /
  - GET /health
- Uses lifespan hook to preload sample data and close storage.

### 3.2 api/dependencies.py
- Maintains global singleton-like instances:
  - _storage: SQLiteStorage
  - _manager: HabitManager
- get_storage() returns SQLiteStorage("habits.db").
- get_habit_manager() yields a HabitManager bound to shared storage.

### 3.3 api/routes.py
Router prefix: /api

Habit endpoints:
- POST /habits
- GET /habits
- GET /habits/{habit_id}
- PUT /habits/{habit_id}
- DELETE /habits/{habit_id}

Completion endpoint:
- POST /habits/{habit_id}/complete

Analytics endpoints:
- GET /analytics/summary
- GET /analytics/longest-streak
- GET /analytics/struggling?days=30
- GET /analytics/by-periodicity/{periodicity}

Notable behavior:
- Duplicate completion for same period returns HTTP 200 with a message payload instead of throwing.
- Query validation enforces periodicity as daily|weekly where defined.

### 3.4 models/habit.py (Domain Model)
Habit object fields:
- id
- name
- description
- periodicity (daily|weekly)
- created_at
- completions (datetime list)

Core domain logic:
- complete_task() blocks duplicate completion in same period.
- get_current_streak() calculates active streak against current/previous period.
- get_longest_streak() calculates historical maximum streak.
- is_broken() detects missed required period.
- to_dict()/from_dict() helpers for serialization.

### 3.5 models/api_models.py (Pydantic Contracts)
Request models:
- HabitCreate
- HabitUpdate
- CompletionCreate

Response models:
- HabitResponse
- HabitListResponse
- AnalyticsResponse

Validation highlights:
- Name and description length constraints.
- Periodicity regex and validator constraints.
- Name trimming and whitespace-only rejection on create.

### 3.6 core/habit_manager.py (Application Service)
Responsibilities:
- Central orchestration of habit operations.
- In-memory cache of habits keyed by id.
- Delegation to storage implementation for persistence.

Key operations:
- create_habit
- get_habit
- get_all_habits
- update_habit
- delete_habit
- complete_habit
- get_habits_by_periodicity

### 3.7 storage/interface.py
Defines abstract contract for storage backends:
- save_habit
- load_habit
- load_all_habits
- update_habit
- delete_habit
- save_completion
- load_completions
- close

### 3.8 storage/sqlite_storage.py
SQLite implementation details:
- Uses sqlite3 with check_same_thread=False.
- Creates tables on initialization:
  - habits
  - completions
- Adds index idx_completions_habit_id.
- Loads completions per habit and rehydrates Habit domain objects.

Schema notes:
- habits.periodicity has CHECK constraint for daily|weekly.
- completions references habits(id) with ON DELETE CASCADE.

### 3.9 analytics/analytics.py
Functional analytics utilities:
- get_all_habits
- get_habits_by_periodicity
- get_longest_streak_all
- get_longest_streak_for_habit
- get_struggling_habits
- get_analytics_summary
- get_completion_rate_by_habit

Computation style:
- Uses map/filter/reduce heavily.
- Struggling habits default threshold is completion rate < 50% over lookback window.

### 3.10 fixtures/sample_data.py
Seed generation:
- Creates 5 predefined habits across daily and weekly periodicities.
- Simulates recent completions with probabilistic patterns.
- Intended for development/demo startup.

### 3.11 cli/controller.py
Provides Click command group and operations:
- create
- list
- complete
- delete
- info
- analyze
- longest

Important dependency note:
- Uses tabulate package, but tabulate is not listed in requirements.txt.
- CLI may fail in clean environments unless tabulate is installed.

## 4. API Contract Summary

### 4.1 Habit Create
- Method: POST
- Path: /api/habits
- Body: name, description, periodicity
- Returns: HabitResponse

### 4.2 Habit List
- Method: GET
- Path: /api/habits
- Query: periodicity (optional)
- Returns: HabitListResponse

### 4.3 Habit Completion
- Method: POST
- Path: /api/habits/{habit_id}/complete
- Body: completed_at (optional)
- Returns: HabitResponse or duplicate-period message payload

### 4.4 Analytics Summary
- Method: GET
- Path: /api/analytics/summary
- Returns:
  - total_habits
  - daily_habits
  - weekly_habits
  - longest_streak_habit
  - longest_streak_days
  - total_completions
  - average_streak

## 5. Data Persistence and Environment

Database file:
- Default local db path: habits.db

Containerized deployment:
- docker-compose maps persistent volume at /app/data.
- compose sets DATABASE_URL, but current Python code does not read it.
- dependencies.py currently hardcodes SQLiteStorage("habits.db").

Operational implication:
- In-container runtime may not use configured DATABASE_URL path unless code is updated.

## 6. Testing

Current test suite includes:
- test_habit.py: domain and streak behavior.
- test_storage.py: SQLite persistence operations.
- test_analytics.py: analytics calculations.
- test_api.py currently duplicates analytics tests rather than API integration tests.

Observed quality notes:
- API endpoint behavior is not directly covered by HTTP-level tests in current state.
- test_api.py appears misnamed/content-duplicated.

## 7. Build, Run, and Tooling

Install dependencies:
- pip install -r requirements.txt

Run API:
- python main.py
or
- uvicorn main:app --host 0.0.0.0 --port 8000 --reload

Run tests:
- pytest
- pytest --cov=.

Docker:
- backend/Dockerfile uses python:3.12-slim and runs uvicorn main:app.
