"""Unit tests for the Habit class."""

import pytest
from datetime import datetime, timedelta
from models.habit import Habit


class TestHabitCreation:
    """Tests for habit creation."""
    
    def test_create_daily_habit(self):
        """Test creating a daily habit."""
        habit = Habit(
            name="Exercise",
            description="30 min workout",
            periodicity="daily"
        )
        
        assert habit.name == "Exercise"
        assert habit.description == "30 min workout"
        assert habit.periodicity == "daily"
        assert habit.id is None
        assert len(habit.completions) == 0
    
    def test_create_weekly_habit(self):
        """Test creating a weekly habit."""
        habit = Habit(
            name="Grocery Shopping",
            description="Buy groceries",
            periodicity="weekly"
        )
        
        assert habit.name == "Grocery Shopping"
        assert habit.periodicity == "weekly"
    
    def test_invalid_periodicity(self):
        """Test that invalid periodicity raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            Habit(
                name="Test",
                description="Test habit",
                periodicity="monthly"
            )
        
        assert "Invalid periodicity" in str(exc_info.value)
    
    def test_habit_with_custom_created_at(self):
        """Test creating a habit with custom creation date."""
        custom_date = datetime(2024, 1, 1, 10, 0, 0)
        habit = Habit(
            name="Test",
            description="Test habit",
            periodicity="daily",
            created_at=custom_date
        )
        
        assert habit.created_at == custom_date
    
    def test_habit_with_id(self):
        """Test creating a habit with an ID."""
        habit = Habit(
            name="Test",
            description="Test habit",
            periodicity="daily",
            habit_id=42
        )
        
        assert habit.id == 42


class TestHabitCompletion:
    """Tests for habit completion functionality."""
    
    def test_complete_task(self):
        """Test completing a task."""
        habit = Habit(
            name="Exercise",
            description="30 min workout",
            periodicity="daily"
        )
        
        result = habit.complete_task()
        
        assert result is True
        assert len(habit.completions) == 1
    
    def test_complete_task_with_date(self):
        """Test completing a task with specific date."""
        habit = Habit(
            name="Exercise",
            description="30 min workout",
            periodicity="daily"
        )
        
        completion_date = datetime(2024, 1, 15, 10, 30, 0)
        result = habit.complete_task(completion_date)
        
        assert result is True
        assert len(habit.completions) == 1
        assert habit.completions[0] == completion_date
    
    def test_duplicate_completion_same_day(self):
        """Test that duplicate completions for same day are prevented."""
        habit = Habit(
            name="Exercise",
            description="30 min workout",
            periodicity="daily"
        )
        
        today = datetime.now().replace(hour=10, minute=0)
        habit.complete_task(today)
        result = habit.complete_task(today.replace(hour=15, minute=0))
        
        assert result is False
        assert len(habit.completions) == 1
    
    def test_completions_different_days(self):
        """Test completions on different days."""
        habit = Habit(
            name="Exercise",
            description="30 min workout",
            periodicity="daily"
        )
        
        day1 = datetime(2024, 1, 15, 10, 0)
        day2 = datetime(2024, 1, 16, 10, 0)
        
        habit.complete_task(day1)
        habit.complete_task(day2)
        
        assert len(habit.completions) == 2
    
    def test_completions_sorted(self):
        """Test that completions are sorted chronologically."""
        habit = Habit(
            name="Exercise",
            description="30 min workout",
            periodicity="daily"
        )
        
        day3 = datetime(2024, 1, 17, 10, 0)
        day1 = datetime(2024, 1, 15, 10, 0)
        day2 = datetime(2024, 1, 16, 10, 0)
        
        habit.complete_task(day3)
        habit.complete_task(day1)
        habit.complete_task(day2)
        
        assert habit.completions[0] == day1
        assert habit.completions[1] == day2
        assert habit.completions[2] == day3


class TestStreakCalculation:
    """Tests for streak calculation."""
    
    def test_no_completions_zero_streak(self):
        """Test that no completions means zero streak."""
        habit = Habit(
            name="Exercise",
            description="30 min workout",
            periodicity="daily"
        )
        
        assert habit.get_current_streak() == 0
        assert habit.get_longest_streak() == 0
    
    def test_single_completion_streak(self):
        """Test streak with single completion today."""
        habit = Habit(
            name="Exercise",
            description="30 min workout",
            periodicity="daily"
        )
        
        habit.complete_task(datetime.now())
        
        assert habit.get_current_streak() == 1
        assert habit.get_longest_streak() == 1
    
    def test_consecutive_days_streak(self):
        """Test streak with consecutive daily completions."""
        habit = Habit(
            name="Exercise",
            description="30 min workout",
            periodicity="daily"
        )
        
        today = datetime.now()
        for i in range(5):
            completion_date = today - timedelta(days=i)
            habit.complete_task(completion_date)
        
        assert habit.get_current_streak() == 5
        assert habit.get_longest_streak() == 5
    
    def test_broken_streak(self):
        """Test that missing a day breaks the streak."""
        habit = Habit(
            name="Exercise",
            description="30 min workout",
            periodicity="daily"
        )
        
        today = datetime.now()
        
        # Complete today and yesterday
        habit.complete_task(today)
        habit.complete_task(today - timedelta(days=1))
        
        # Skip a day and complete 3 days ago
        habit.complete_task(today - timedelta(days=3))
        
        # Current streak should be 2 (today + yesterday)
        assert habit.get_current_streak() == 2
    
    def test_longest_streak_historical(self):
        """Test that longest streak can be historical."""
        habit = Habit(
            name="Exercise",
            description="30 min workout",
            periodicity="daily"
        )
        
        today = datetime.now()
        
        # Current streak of 2
        habit.complete_task(today)
        habit.complete_task(today - timedelta(days=1))
        
        # Gap
        
        # Historical streak of 5 (days 10-14 ago)
        for i in range(10, 15):
            habit.complete_task(today - timedelta(days=i))
        
        assert habit.get_current_streak() == 2
        assert habit.get_longest_streak() == 5
    
    def test_weekly_streak(self):
        """Test streak calculation for weekly habits."""
        habit = Habit(
            name="Groceries",
            description="Weekly shopping",
            periodicity="weekly"
        )
        
        today = datetime.now()
        
        # Complete for 4 consecutive weeks
        for i in range(4):
            habit.complete_task(today - timedelta(weeks=i))
        
        assert habit.get_current_streak() == 4
        assert habit.get_longest_streak() == 4


class TestHabitBroken:
    """Tests for habit broken status."""
    
    def test_new_habit_not_broken_immediately(self):
        """Test that a new habit is not immediately broken."""
        habit = Habit(
            name="Exercise",
            description="30 min workout",
            periodicity="daily",
            created_at=datetime.now()
        )
        
        assert habit.is_broken() is False
    
    def test_habit_broken_after_missed_period(self):
        """Test that a habit is broken after missing a period."""
        habit = Habit(
            name="Exercise",
            description="30 min workout",
            periodicity="daily",
            created_at=datetime.now() - timedelta(days=3)
        )
        
        # No completions for 3 days
        assert habit.is_broken() is True
    
    def test_habit_not_broken_with_recent_completion(self):
        """Test that a habit is not broken with recent completion."""
        habit = Habit(
            name="Exercise",
            description="30 min workout",
            periodicity="daily"
        )
        
        habit.complete_task(datetime.now())
        
        assert habit.is_broken() is False


class TestHabitSerialization:
    """Tests for habit serialization."""
    
    def test_to_dict(self):
        """Test converting habit to dictionary."""
        habit = Habit(
            name="Exercise",
            description="30 min workout",
            periodicity="daily",
            habit_id=1,
            created_at=datetime(2024, 1, 1, 10, 0, 0)
        )
        
        habit.complete_task(datetime(2024, 1, 2, 10, 0, 0))
        
        data = habit.to_dict()
        
        assert data["id"] == 1
        assert data["name"] == "Exercise"
        assert data["description"] == "30 min workout"
        assert data["periodicity"] == "daily"
        assert data["created_at"] == "2024-01-01T10:00:00"
        assert len(data["completions"]) == 1
        assert "current_streak" in data
        assert "longest_streak" in data
    
    def test_from_dict(self):
        """Test creating habit from dictionary."""
        data = {
            "id": 1,
            "name": "Exercise",
            "description": "30 min workout",
            "periodicity": "daily",
            "created_at": "2024-01-01T10:00:00",
            "completions": ["2024-01-02T10:00:00"]
        }
        
        habit = Habit.from_dict(data)
        
        assert habit.id == 1
        assert habit.name == "Exercise"
        assert habit.description == "30 min workout"
        assert habit.periodicity == "daily"
        assert len(habit.completions) == 1
    
    def test_repr(self):
        """Test string representation of habit."""
        habit = Habit(
            name="Exercise",
            description="30 min workout",
            periodicity="daily",
            habit_id=1
        )
        
        repr_str = repr(habit)
        
        assert "Exercise" in repr_str
        assert "daily" in repr_str