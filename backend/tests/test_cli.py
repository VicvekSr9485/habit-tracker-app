"""Tests for the Click-based CLI entry point.

The CLI module instantiates a module-level :class:`SQLiteStorage` against
``habits.db`` at import time, which is awkward to test in isolation. Each
test patches the module-level ``manager`` with a fresh in-memory-backed
:class:`HabitManager` so commands run against an isolated database.
"""

from unittest.mock import patch

import pytest
from click.testing import CliRunner

from cli import controller as cli_module
from core.habit_manager import HabitManager
from storage.sqlite_storage import SQLiteStorage


@pytest.fixture
def runner():
    """Provide a Click :class:`CliRunner` for invoking commands."""
    return CliRunner()


@pytest.fixture
def cli_manager(tmp_path, monkeypatch):
    """Replace the CLI's module-level manager with a temp-DB-backed one."""
    db_path = tmp_path / "cli.db"
    storage = SQLiteStorage(str(db_path))
    manager = HabitManager(storage)
    monkeypatch.setattr(cli_module, "manager", manager)
    yield manager
    storage.close()


class TestCreateCommand:
    def test_create_succeeds(self, runner, cli_manager):
        result = runner.invoke(
            cli_module.cli,
            [
                "create",
                "--name", "Stretch",
                "--description", "5 min stretch",
                "--periodicity", "daily",
            ],
        )
        assert result.exit_code == 0
        assert "Habit created successfully" in result.output
        assert len(cli_manager.get_all_habits()) == 1


class TestListCommand:
    def test_list_empty(self, runner, cli_manager):
        result = runner.invoke(cli_module.cli, ["list"])
        assert result.exit_code == 0
        assert "No" in result.output and "habits found" in result.output

    def test_list_populated(self, runner, cli_manager):
        cli_manager.create_habit("Read", "Read a book", "daily")
        cli_manager.create_habit("Plan", "Plan the week", "weekly")

        result = runner.invoke(cli_module.cli, ["list"])
        assert result.exit_code == 0
        assert "Read" in result.output
        assert "Plan" in result.output

    def test_list_filtered_by_periodicity(self, runner, cli_manager):
        cli_manager.create_habit("Read", "Read a book", "daily")
        cli_manager.create_habit("Plan", "Plan the week", "weekly")

        result = runner.invoke(
            cli_module.cli, ["list", "--periodicity", "weekly"]
        )
        assert result.exit_code == 0
        assert "Plan" in result.output
        assert "Read" not in result.output


class TestCompleteCommand:
    def test_complete_unknown_habit(self, runner, cli_manager):
        result = runner.invoke(cli_module.cli, ["complete", "999"])
        assert result.exit_code == 0
        assert "not found" in result.output

    def test_complete_success(self, runner, cli_manager):
        habit = cli_manager.create_habit("Hydrate", "drink water", "daily")
        result = runner.invoke(cli_module.cli, ["complete", str(habit.id)])
        assert result.exit_code == 0
        assert "completed" in result.output.lower()

    def test_complete_already_done(self, runner, cli_manager):
        habit = cli_manager.create_habit("Hydrate", "drink water", "daily")
        cli_manager.complete_habit(habit.id)

        result = runner.invoke(cli_module.cli, ["complete", str(habit.id)])
        assert result.exit_code == 0
        assert "already completed" in result.output


class TestDeleteCommand:
    def test_delete_unknown_habit(self, runner, cli_manager):
        result = runner.invoke(cli_module.cli, ["delete", "999"])
        assert result.exit_code == 0
        assert "not found" in result.output

    def test_delete_confirmed(self, runner, cli_manager):
        habit = cli_manager.create_habit("Read", "books", "daily")

        result = runner.invoke(
            cli_module.cli, ["delete", str(habit.id)], input="y\n"
        )
        assert result.exit_code == 0
        assert "deleted successfully" in result.output
        assert cli_manager.get_habit(habit.id) is None

    def test_delete_cancelled(self, runner, cli_manager):
        habit = cli_manager.create_habit("Read", "books", "daily")

        result = runner.invoke(
            cli_module.cli, ["delete", str(habit.id)], input="n\n"
        )
        assert result.exit_code == 0
        assert "Cancelled" in result.output
        assert cli_manager.get_habit(habit.id) is not None


class TestInfoCommand:
    def test_info_unknown_habit(self, runner, cli_manager):
        result = runner.invoke(cli_module.cli, ["info", "999"])
        assert result.exit_code == 0
        assert "not found" in result.output

    def test_info_with_completions(self, runner, cli_manager):
        habit = cli_manager.create_habit("Read", "Read a book", "daily")
        cli_manager.complete_habit(habit.id)

        result = runner.invoke(cli_module.cli, ["info", str(habit.id)])
        assert result.exit_code == 0
        assert "Read" in result.output
        assert "Recent Completions" in result.output


class TestAnalyzeCommand:
    def test_analyze_no_habits(self, runner, cli_manager):
        result = runner.invoke(cli_module.cli, ["analyze"])
        assert result.exit_code == 0
        assert "No habits to analyze" in result.output

    def test_analyze_with_habits(self, runner, cli_manager):
        habit = cli_manager.create_habit("Read", "books", "daily")
        cli_manager.complete_habit(habit.id)

        result = runner.invoke(cli_module.cli, ["analyze"])
        assert result.exit_code == 0
        assert "Total Habits" in result.output


class TestLongestCommand:
    def test_longest_no_habits(self, runner, cli_manager):
        result = runner.invoke(cli_module.cli, ["longest"])
        assert result.exit_code == 0
        assert "No habits found" in result.output

    def test_longest_with_streak(self, runner, cli_manager):
        habit = cli_manager.create_habit("Read", "books", "daily")
        cli_manager.complete_habit(habit.id)

        result = runner.invoke(cli_module.cli, ["longest"])
        assert result.exit_code == 0
        assert "Longest Streak" in result.output or "No streaks" in result.output
