"""Integration-style tests for FastAPI habit endpoints."""

from datetime import datetime

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routes import router
from api.dependencies import get_habit_manager
from core.habit_manager import HabitManager
from storage.sqlite_storage import SQLiteStorage


@pytest.fixture
def manager(tmp_path):
    """Create a manager backed by a temporary SQLite database."""
    db_path = tmp_path / "api_test.db"
    storage = SQLiteStorage(str(db_path))
    habit_manager = HabitManager(storage)
    yield habit_manager
    storage.close()


@pytest.fixture
def client(manager):
    """Create a test client with dependency overrides."""
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_habit_manager] = lambda: manager

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def _create_habit(client: TestClient, name: str = "Exercise") -> dict:
    response = client.post(
        "/api/habits",
        json={
            "name": name,
            "description": "30 minutes workout",
            "periodicity": "daily",
        },
    )
    assert response.status_code == 201
    return response.json()


class TestHabitEndpoints:
    """Tests for habit CRUD and completion endpoints."""

    def test_create_habit(self, client):
        habit = _create_habit(client)

        assert habit["id"] > 0
        assert habit["name"] == "Exercise"
        assert habit["periodicity"] == "daily"
        assert habit["completion_count"] == 0

    def test_list_habits(self, client):
        _create_habit(client, name="Exercise")
        _create_habit(client, name="Read")

        response = client.get("/api/habits")
        assert response.status_code == 200

        payload = response.json()
        assert payload["total"] == 2
        assert len(payload["habits"]) == 2

    def test_get_habit_by_id(self, client):
        habit = _create_habit(client)

        response = client.get(f"/api/habits/{habit['id']}")
        assert response.status_code == 200
        assert response.json()["id"] == habit["id"]

    def test_update_habit(self, client):
        habit = _create_habit(client)

        response = client.put(
            f"/api/habits/{habit['id']}",
            json={
                "name": "Updated Exercise",
                "description": "Updated description",
                "periodicity": "weekly",
            },
        )
        assert response.status_code == 200

        updated = response.json()
        assert updated["name"] == "Updated Exercise"
        assert updated["periodicity"] == "weekly"

    def test_complete_habit(self, client):
        habit = _create_habit(client)

        response = client.post(
            f"/api/habits/{habit['id']}/complete",
            json={"completed_at": datetime.now().isoformat()},
        )
        assert response.status_code == 200

        completed = response.json()
        assert completed["id"] == habit["id"]
        assert completed["completion_count"] == 1

    def test_delete_habit(self, client):
        habit = _create_habit(client)

        delete_response = client.delete(f"/api/habits/{habit['id']}")
        assert delete_response.status_code == 204

        get_response = client.get(f"/api/habits/{habit['id']}")
        assert get_response.status_code == 404


class TestAnalyticsEndpoints:
    """Tests for analytics endpoints."""

    def test_analytics_summary(self, client):
        habit = _create_habit(client)
        client.post(f"/api/habits/{habit['id']}/complete", json={})

        response = client.get("/api/analytics/summary")
        assert response.status_code == 200

        payload = response.json()
        assert payload["total_habits"] == 1
        assert payload["daily_habits"] == 1
        assert payload["total_completions"] == 1

    def test_longest_streak_endpoint(self, client):
        _create_habit(client, name="Exercise")

        response = client.get("/api/analytics/longest-streak")
        assert response.status_code == 200

        payload = response.json()
        assert "habit_name" in payload
        assert "longest_streak" in payload

    def test_struggling_habits_endpoint(self, client):
        _create_habit(client, name="Exercise")

        response = client.get("/api/analytics/struggling?days=14")
        assert response.status_code == 200

        payload = response.json()
        assert payload["period_days"] == 14
        assert "struggling_habits" in payload

    def test_analytics_by_periodicity_validation(self, client):
        response = client.get("/api/analytics/by-periodicity/monthly")

        assert response.status_code == 400
        assert "daily" in response.json()["detail"]
