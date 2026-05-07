"""Edge-case tests covering empty inputs, period boundaries and concurrency.

These tests intentionally focus on the seams the rest of the suite glosses
over: zero-length collections, completions that straddle a day or ISO-week
boundary, and concurrent calls into the manager from multiple threads.
"""

import os
import tempfile
import threading
from datetime import datetime, timedelta

import pytest

from analytics import analytics
from core.habit_manager import HabitManager
from fixtures.sample_data import generate_sample_habits, load_sample_data
from models.habit import Habit
from storage.sqlite_storage import SQLiteStorage


@pytest.fixture
def storage(tmp_path):
    """Provide a SQLite-backed storage instance pinned to a temp file."""
    db_path = tmp_path / "edge.db"
    storage = SQLiteStorage(str(db_path))
    yield storage
    storage.close()


@pytest.fixture
def manager(storage):
    """Provide a HabitManager backed by the temp storage fixture."""
    return HabitManager(storage)


class TestEmptyCollections:
    """Behaviour when habits or completions are empty."""

    def test_manager_with_no_habits(self, manager):
        assert manager.get_all_habits() == []
        assert manager.get_habit(1) is None
        assert manager.get_habits_by_periodicity("daily") == []

    def test_complete_unknown_habit_returns_false(self, manager):
        assert manager.complete_habit(9999) is False

    def test_update_unknown_habit_returns_none(self, manager):
        assert manager.update_habit(9999, name="x") is None

    def test_delete_unknown_habit_returns_false(self, manager):
        assert manager.delete_habit(9999) is False

    def test_analytics_summary_on_empty_list(self):
        summary = analytics.get_analytics_summary([])
        assert summary["total_habits"] == 0
        assert summary["longest_streak_habit"] is None
        assert summary["average_streak"] == 0.0

    def test_completion_rate_on_empty_list(self):
        assert analytics.get_completion_rate_by_habit([]) == []

    def test_struggling_habits_on_empty_list(self):
        assert analytics.get_struggling_habits([]) == []

    def test_habit_to_dict_with_no_completions(self):
        habit = Habit(name="x", description="y", periodicity="daily")
        data = habit.to_dict()
        assert data["completions"] == []
        assert data["current_streak"] == 0
        assert data["longest_streak"] == 0


class TestPeriodBoundaries:
    """Streak and completion logic around day/week boundaries."""

    def test_two_completions_same_day_count_once(self):
        habit = Habit(name="Drink water", description="", periodicity="daily")
        morning = datetime(2026, 5, 7, 7, 0)
        evening = datetime(2026, 5, 7, 21, 0)

        assert habit.complete_task(morning) is True
        assert habit.complete_task(evening) is False
        assert len(habit.completions) == 1

    def test_completions_across_midnight_count_separately(self):
        habit = Habit(name="Stretch", description="", periodicity="daily")
        late_night = datetime(2026, 5, 6, 23, 59)
        next_morning = datetime(2026, 5, 7, 0, 1)

        assert habit.complete_task(late_night) is True
        assert habit.complete_task(next_morning) is True
        assert len(habit.completions) == 2

    def test_iso_week_boundary_for_weekly_habit(self):
        """ISO weeks roll over on Monday — a Sunday/Monday pair are
        in different periods even though only one day apart."""
        habit = Habit(name="Plan", description="", periodicity="weekly")
        sunday = datetime(2026, 1, 4, 18, 0)
        monday = datetime(2026, 1, 5, 9, 0)

        assert habit.complete_task(sunday) is True
        assert habit.complete_task(monday) is True
        assert len(habit.completions) == 2

    def test_same_iso_week_different_days_count_once(self):
        habit = Habit(name="Plan", description="", periodicity="weekly")
        monday = datetime(2026, 1, 5, 9, 0)
        wednesday = datetime(2026, 1, 7, 9, 0)

        assert habit.complete_task(monday) is True
        assert habit.complete_task(wednesday) is False
        assert len(habit.completions) == 1

    def test_year_boundary_streak(self):
        """A daily streak crossing 31 Dec → 1 Jan must remain unbroken."""
        habit = Habit(name="Journal", description="", periodicity="daily")
        habit.complete_task(datetime(2025, 12, 31, 9, 0))
        habit.complete_task(datetime(2026, 1, 1, 9, 0))
        habit.complete_task(datetime(2026, 1, 2, 9, 0))

        assert habit.get_longest_streak() == 3

    def test_is_broken_after_one_full_period_gap(self):
        habit = Habit(
            name="Walk",
            description="",
            periodicity="daily",
            created_at=datetime.now() - timedelta(days=5),
        )
        habit.complete_task(datetime.now() - timedelta(days=4))
        assert habit.is_broken() is True


class TestConcurrentCompletions:
    """Concurrency safety of HabitManager.complete_habit."""

    def test_concurrent_complete_keeps_one_record_per_period(self, manager):
        habit = manager.create_habit(
            name="Hydrate",
            description="Drink water",
            periodicity="daily",
        )

        target_time = datetime.now().replace(hour=12, minute=0, second=0, microsecond=0)
        results: list[bool] = []
        results_lock = threading.Lock()

        def worker():
            outcome = manager.complete_habit(habit.id, target_time)
            with results_lock:
                results.append(outcome)

        threads = [threading.Thread(target=worker) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Domain-level dedupe: at most one completion is recorded for the
        # period regardless of how many threads raced.
        reloaded = manager.get_habit(habit.id)
        assert len(reloaded.completions) == 1
        assert sum(1 for r in results if r) == 1

    def test_concurrent_complete_distinct_periods(self, manager):
        habit = manager.create_habit(
            name="Read",
            description="Read a book",
            periodicity="daily",
        )

        days = [datetime.now() - timedelta(days=i) for i in range(5)]

        def worker(when: datetime):
            manager.complete_habit(habit.id, when)

        threads = [threading.Thread(target=worker, args=(d,)) for d in days]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        reloaded = manager.get_habit(habit.id)
        assert len(reloaded.completions) == 5


class TestFixtureLoading:
    """Sample-data fixtures used to bootstrap demo databases."""

    def test_generate_sample_habits_returns_five(self):
        habits = generate_sample_habits()
        assert len(habits) == 5
        names = {h.name for h in habits}
        assert "Morning Exercise" in names
        assert "Weekly Grocery Shopping" in names

    def test_sample_habits_have_completions(self):
        habits = generate_sample_habits()
        # At least the deterministic weekly grocery habit gets four entries.
        groceries = next(h for h in habits if h.name == "Weekly Grocery Shopping")
        assert len(groceries.completions) == 4

    def test_load_sample_data_persists_to_storage(self, storage, capsys):
        load_sample_data(storage)
        loaded = storage.load_all_habits()
        assert len(loaded) == 5
        # The loader prints a status line per habit; ensure it ran.
        captured = capsys.readouterr()
        assert "Loaded sample habit" in captured.out


class TestStorageDatetimeRoundTrip:
    """Datetime adapter/converter round-trips after the Python 3.12 fix."""

    def test_microseconds_survive_round_trip(self, storage):
        habit = Habit(name="x", description="y", periodicity="daily")
        precise = datetime(2026, 5, 7, 12, 0, 0, 123_456)
        habit.complete_task(precise)

        habit_id = storage.save_habit(habit)
        reloaded = storage.load_habit(habit_id)

        assert reloaded.completions[0] == precise

    def test_naive_datetime_survives_round_trip(self, storage):
        created = datetime(2026, 1, 1, 0, 0, 0)
        habit = Habit(
            name="x",
            description="y",
            periodicity="daily",
            created_at=created,
        )
        habit_id = storage.save_habit(habit)
        reloaded = storage.load_habit(habit_id)

        assert reloaded.created_at == created
