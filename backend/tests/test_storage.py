"""Unit tests for storage implementations."""

import pytest
import os
import tempfile
from datetime import datetime, timedelta
from storage.sqlite_storage import SQLiteStorage
from models.habit import Habit


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    # Cleanup
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
def storage(temp_db):
    """Create a storage instance with temporary database."""
    storage = SQLiteStorage(temp_db)
    yield storage
    storage.close()


class TestSQLiteStorage:
    """Tests for SQLite storage implementation."""
    
    def test_save_and_load_habit(self, storage):
        """Test saving and loading a habit."""
        habit = Habit(
            name="Exercise",
            description="30 min workout",
            periodicity="daily"
        )
        
        habit_id = storage.save_habit(habit)
        loaded_habit = storage.load_habit(habit_id)
        
        assert loaded_habit is not None
        assert loaded_habit.id == habit_id
        assert loaded_habit.name == "Exercise"
        assert loaded_habit.description == "30 min workout"
        assert loaded_habit.periodicity == "daily"
    
    def test_load_nonexistent_habit(self, storage):
        """Test loading a habit that doesn't exist."""
        result = storage.load_habit(999)
        
        assert result is None
    
    def test_load_all_habits_empty(self, storage):
        """Test loading all habits when database is empty."""
        habits = storage.load_all_habits()
        
        assert len(habits) == 0
    
    def test_load_all_habits(self, storage):
        """Test loading all habits."""
        habit1 = Habit(
            name="Exercise",
            description="30 min workout",
            periodicity="daily"
        )
        habit2 = Habit(
            name="Reading",
            description="Read books",
            periodicity="daily"
        )
        
        storage.save_habit(habit1)
        storage.save_habit(habit2)
        
        habits = storage.load_all_habits()
        
        assert len(habits) == 2
    
    def test_update_habit(self, storage):
        """Test updating a habit."""
        habit = Habit(
            name="Exercise",
            description="30 min workout",
            periodicity="daily"
        )
        
        habit_id = storage.save_habit(habit)
        habit.id = habit_id
        habit.name = "Updated Exercise"
        habit.description = "Updated description"
        
        success = storage.update_habit(habit)
        loaded_habit = storage.load_habit(habit_id)
        
        assert success is True
        assert loaded_habit.name == "Updated Exercise"
        assert loaded_habit.description == "Updated description"
    
    def test_delete_habit(self, storage):
        """Test deleting a habit."""
        habit = Habit(
            name="Exercise",
            description="30 min workout",
            periodicity="daily"
        )
        
        habit_id = storage.save_habit(habit)
        success = storage.delete_habit(habit_id)
        loaded_habit = storage.load_habit(habit_id)
        
        assert success is True
        assert loaded_habit is None
    
    def test_delete_nonexistent_habit(self, storage):
        """Test deleting a habit that doesn't exist."""
        success = storage.delete_habit(999)
        
        assert success is False
    
    def test_save_and_load_completions(self, storage):
        """Test saving and loading completions."""
        habit = Habit(
            name="Exercise",
            description="30 min workout",
            periodicity="daily"
        )
        
        habit_id = storage.save_habit(habit)
        
        completion1 = datetime(2024, 1, 15, 10, 0, 0)
        completion2 = datetime(2024, 1, 16, 10, 0, 0)
        
        storage.save_completion(habit_id, completion1)
        storage.save_completion(habit_id, completion2)
        
        completions = storage.load_completions(habit_id)
        
        assert len(completions) == 2
        assert completion1 in completions
        assert completion2 in completions
    
    def test_save_habit_with_completions(self, storage):
        """Test saving a habit that already has completions."""
        habit = Habit(
            name="Exercise",
            description="30 min workout",
            periodicity="daily"
        )
        
        habit.complete_task(datetime(2024, 1, 15, 10, 0, 0))
        habit.complete_task(datetime(2024, 1, 16, 10, 0, 0))
        
        habit_id = storage.save_habit(habit)
        loaded_habit = storage.load_habit(habit_id)
        
        assert len(loaded_habit.completions) == 2
    
    def test_habit_completions_loaded_correctly(self, storage):
        """Test that habit completions are loaded with habit."""
        habit = Habit(
            name="Exercise",
            description="30 min workout",
            periodicity="daily"
        )
        
        habit_id = storage.save_habit(habit)
        
        completion = datetime(2024, 1, 15, 10, 0, 0)
        storage.save_completion(habit_id, completion)
        
        loaded_habit = storage.load_habit(habit_id)
        
        assert len(loaded_habit.completions) == 1
        assert loaded_habit.completions[0] == completion


class TestStorageEdgeCases:
    """Tests for edge cases in storage."""
    
    def test_multiple_saves_same_habit(self, storage):
        """Test that saving creates new records each time."""
        habit = Habit(
            name="Exercise",
            description="30 min workout",
            periodicity="daily"
        )
        
        id1 = storage.save_habit(habit)
        id2 = storage.save_habit(habit)
        
        assert id1 != id2
    
    def test_habit_ordering(self, storage):
        """Test that habits are returned in order."""
        for i in range(5):
            habit = Habit(
                name=f"Habit {i}",
                description=f"Description {i}",
                periodicity="daily"
            )
            storage.save_habit(habit)
        
        habits = storage.load_all_habits()
        
        assert len(habits) == 5