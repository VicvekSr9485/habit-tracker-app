"""Unit tests for the analytics module."""

import pytest
from datetime import datetime, timedelta
from models.habit import Habit
from analytics import analytics


@pytest.fixture
def sample_habits():
    """Create sample habits for testing."""
    base_date = datetime.now() - timedelta(days=28)
    
    # Daily habit with good streak
    exercise = Habit(
        name="Exercise",
        description="30 min workout",
        periodicity="daily",
        habit_id=1,
        created_at=base_date
    )
    
    # Add completions for 14 consecutive days
    for i in range(14):
        completion = datetime.now() - timedelta(days=i)
        exercise.complete_task(completion)
    
    # Daily habit with poor streak
    reading = Habit(
        name="Reading",
        description="Read 30 min",
        periodicity="daily",
        habit_id=2,
        created_at=base_date
    )
    
    # Add sporadic completions
    reading.complete_task(datetime.now())
    reading.complete_task(datetime.now() - timedelta(days=5))
    reading.complete_task(datetime.now() - timedelta(days=10))
    
    # Weekly habit
    groceries = Habit(
        name="Groceries",
        description="Weekly shopping",
        periodicity="weekly",
        habit_id=3,
        created_at=base_date
    )
    
    # Complete for 3 weeks
    for i in range(3):
        groceries.complete_task(datetime.now() - timedelta(weeks=i))
    
    return [exercise, reading, groceries]


class TestGetAllHabits:
    """Tests for get_all_habits function."""
    
    def test_returns_all_habits(self, sample_habits):
        """Test that all habits are returned."""
        result = analytics.get_all_habits(sample_habits)
        
        assert len(result) == 3
    
    def test_habit_data_structure(self, sample_habits):
        """Test the structure of returned habit data."""
        result = analytics.get_all_habits(sample_habits)
        
        for habit_data in result:
            assert "id" in habit_data
            assert "name" in habit_data
            assert "periodicity" in habit_data
            assert "current_streak" in habit_data
            assert "created_at" in habit_data
    
    def test_empty_list(self):
        """Test with empty habit list."""
        result = analytics.get_all_habits([])
        
        assert len(result) == 0


class TestGetHabitsByPeriodicity:
    """Tests for get_habits_by_periodicity function."""
    
    def test_filter_daily_habits(self, sample_habits):
        """Test filtering daily habits."""
        result = analytics.get_habits_by_periodicity(sample_habits, "daily")
        
        assert len(result) == 2
        for habit in result:
            assert habit.periodicity == "daily"
    
    def test_filter_weekly_habits(self, sample_habits):
        """Test filtering weekly habits."""
        result = analytics.get_habits_by_periodicity(sample_habits, "weekly")
        
        assert len(result) == 1
        assert result[0].periodicity == "weekly"
        assert result[0].name == "Groceries"
    
    def test_no_matching_habits(self, sample_habits):
        """Test when no habits match the filter."""
        # Remove weekly habits
        daily_only = [h for h in sample_habits if h.periodicity == "daily"]
        
        result = analytics.get_habits_by_periodicity(daily_only, "weekly")
        
        assert len(result) == 0


class TestGetLongestStreakAll:
    """Tests for get_longest_streak_all function."""
    
    def test_finds_longest_streak(self, sample_habits):
        """Test finding the longest streak across all habits."""
        habit_name, streak = analytics.get_longest_streak_all(sample_habits)
        
        assert habit_name == "Exercise"
        assert streak == 14
    
    def test_empty_list(self):
        """Test with empty habit list."""
        habit_name, streak = analytics.get_longest_streak_all([])
        
        assert habit_name is None
        assert streak == 0
    
    def test_all_zero_streaks(self):
        """Test when all habits have zero streaks."""
        habits = [
            Habit(
                name="Test1",
                description="Test",
                periodicity="daily",
                habit_id=1
            ),
            Habit(
                name="Test2",
                description="Test",
                periodicity="daily",
                habit_id=2
            )
        ]
        
        habit_name, streak = analytics.get_longest_streak_all(habits)
        
        assert streak == 0


class TestGetLongestStreakForHabit:
    """Tests for get_longest_streak_for_habit function."""
    
    def test_returns_correct_streak(self, sample_habits):
        """Test returning correct streak for a habit."""
        exercise = sample_habits[0]
        
        result = analytics.get_longest_streak_for_habit(exercise)
        
        assert result == 14
    
    def test_no_completions(self):
        """Test with habit that has no completions."""
        habit = Habit(
            name="Test",
            description="Test",
            periodicity="daily"
        )
        
        result = analytics.get_longest_streak_for_habit(habit)
        
        assert result == 0


class TestGetStrugglingHabits:
    """Tests for get_struggling_habits function."""
    
    def test_identifies_struggling_habits(self, sample_habits):
        """Test identifying habits with low completion rates."""
        result = analytics.get_struggling_habits(sample_habits, 30)
        
        # Reading should be struggling (low completion rate)
        struggling_names = [h["name"] for h in result]
        assert "Reading" in struggling_names
    
    def test_returns_sorted_by_rate(self, sample_habits):
        """Test that results are sorted by completion rate."""
        result = analytics.get_struggling_habits(sample_habits, 30)
        
        if len(result) > 1:
            rates = [h["completion_rate"] for h in result]
            assert rates == sorted(rates)
    
    def test_empty_list(self):
        """Test with empty habit list."""
        result = analytics.get_struggling_habits([], 30)
        
        assert len(result) == 0


class TestGetAnalyticsSummary:
    """Tests for get_analytics_summary function."""
    
    def test_summary_structure(self, sample_habits):
        """Test the structure of analytics summary."""
        result = analytics.get_analytics_summary(sample_habits)
        
        assert "total_habits" in result
        assert "daily_habits" in result
        assert "weekly_habits" in result
        assert "longest_streak_habit" in result
        assert "longest_streak_days" in result
        assert "total_completions" in result
        assert "average_streak" in result
    
    def test_summary_values(self, sample_habits):
        """Test correct values in summary."""
        result = analytics.get_analytics_summary(sample_habits)
        
        assert result["total_habits"] == 3
        assert result["daily_habits"] == 2
        assert result["weekly_habits"] == 1
        assert result["longest_streak_habit"] == "Exercise"
        assert result["longest_streak_days"] == 14
    
    def test_empty_summary(self):
        """Test summary with no habits."""
        result = analytics.get_analytics_summary([])
        
        assert result["total_habits"] == 0
        assert result["daily_habits"] == 0
        assert result["weekly_habits"] == 0
        assert result["longest_streak_habit"] is None
        assert result["longest_streak_days"] == 0
        assert result["total_completions"] == 0
        assert result["average_streak"] == 0.0