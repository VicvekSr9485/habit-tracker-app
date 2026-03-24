"""Functional analytics module for habit data analysis."""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple, Optional
from functools import reduce

from models.habit import Habit


def get_all_habits(habits: List[Habit]) -> List[Dict[str, Any]]:
    """
    Get a list of all currently tracked habits.
    
    Args:
        habits: List of Habit objects
    
    Returns:
        List of habit dictionaries with basic information
    """
    return list(map(lambda h: {
        "id": h.id,
        "name": h.name,
        "periodicity": h.periodicity,
        "current_streak": h.get_current_streak(),
        "created_at": h.created_at.isoformat(),
    }, habits))


def get_habits_by_periodicity(
    habits: List[Habit],
    periodicity: str
) -> List[Habit]:
    """
    Filter habits by their periodicity.
    
    Args:
        habits: List of Habit objects
        periodicity: The periodicity to filter by ('daily' or 'weekly')
    
    Returns:
        List of habits matching the specified periodicity
    """
    return list(filter(lambda h: h.periodicity == periodicity, habits))


def get_longest_streak_all(habits: List[Habit]) -> Tuple[Optional[str], int]:
    """
    Find the longest streak across all habits.
    
    Args:
        habits: List of Habit objects
    
    Returns:
        Tuple of (habit_name, longest_streak_count)
        Returns (None, 0) if no habits exist
    """
    if not habits:
        return (None, 0)
    
    # Map each habit to (name, longest_streak)
    habit_streaks = list(map(
        lambda h: (h.name, h.get_longest_streak()),
        habits
    ))
    
    # Reduce to find the maximum
    max_habit = reduce(
        lambda acc, curr: curr if curr[1] > acc[1] else acc,
        habit_streaks,
        ("", 0)
    )
    
    return max_habit if max_habit[0] else (None, 0)


def get_longest_streak_for_habit(habit: Habit) -> int:
    """
    Get the longest streak for a specific habit.
    
    Args:
        habit: The Habit object to analyze
    
    Returns:
        The longest streak count for this habit
    """
    return habit.get_longest_streak()


def get_struggling_habits(
    habits: List[Habit],
    period_days: int = 30
) -> List[Dict[str, Any]]:
    """
    Identify habits with which users struggled (low completion rate).
    
    Args:
        habits: List of Habit objects
        period_days: Number of days to look back (default 30)
    
    Returns:
        List of habits with completion rate below 50%
    """
    cutoff_date = datetime.now() - timedelta(days=period_days)
    
    def calculate_completion_rate(habit: Habit) -> Dict[str, Any]:
        """Calculate completion rate for a habit."""
        # Count expected completions based on periodicity
        days_since_creation = (datetime.now() - max(habit.created_at, cutoff_date)).days
        
        if habit.periodicity == "daily":
            expected = days_since_creation
        else:  # weekly
            expected = days_since_creation // 7
        
        # Count actual completions in period
        actual = len(list(filter(
            lambda c: c >= cutoff_date,
            habit.completions
        )))
        
        rate = (actual / expected * 100) if expected > 0 else 0
        
        return {
            "id": habit.id,
            "name": habit.name,
            "periodicity": habit.periodicity,
            "completion_rate": round(rate, 2),
            "expected": expected,
            "actual": actual,
        }
    
    # Map habits to completion rates
    habits_with_rates = list(map(calculate_completion_rate, habits))
    
    # Filter for struggling habits (< 50% completion rate)
    struggling = list(filter(
        lambda h: h["completion_rate"] < 50,
        habits_with_rates
    ))
    
    # Sort by completion rate (worst first)
    return sorted(struggling, key=lambda h: h["completion_rate"])


def get_analytics_summary(habits: List[Habit]) -> Dict[str, Any]:
    """
    Generate a comprehensive analytics summary.
    
    Args:
        habits: List of Habit objects
    
    Returns:
        Dictionary containing various analytics metrics
    """
    if not habits:
        return {
            "total_habits": 0,
            "daily_habits": 0,
            "weekly_habits": 0,
            "longest_streak_habit": None,
            "longest_streak_days": 0,
            "total_completions": 0,
            "average_streak": 0.0,
        }
    
    daily_habits = get_habits_by_periodicity(habits, "daily")
    weekly_habits = get_habits_by_periodicity(habits, "weekly")
    
    longest_habit_name, longest_streak = get_longest_streak_all(habits)
    
    total_completions = reduce(
        lambda acc, h: acc + len(h.completions),
        habits,
        0
    )
    
    current_streaks = list(map(lambda h: h.get_current_streak(), habits))
    average_streak = (
        sum(current_streaks) / len(current_streaks)
        if current_streaks else 0.0
    )
    
    return {
        "total_habits": len(habits),
        "daily_habits": len(daily_habits),
        "weekly_habits": len(weekly_habits),
        "longest_streak_habit": longest_habit_name,
        "longest_streak_days": longest_streak,
        "total_completions": total_completions,
        "average_streak": round(average_streak, 2),
    }


def get_completion_rate_by_habit(
    habits: List[Habit],
    days: int = 30
) -> List[Dict[str, Any]]:
    """
    Calculate completion rates for all habits over a period.
    
    Args:
        habits: List of Habit objects
        days: Number of days to analyze
    
    Returns:
        List of habits with their completion rates
    """
    cutoff_date = datetime.now() - timedelta(days=days)
    
    def calc_rate(habit: Habit) -> Dict[str, Any]:
        recent_completions = list(filter(
            lambda c: c >= cutoff_date,
            habit.completions
        ))
        
        days_active = (datetime.now() - max(habit.created_at, cutoff_date)).days
        expected = days_active if habit.periodicity == "daily" else days_active // 7
        actual = len(recent_completions)
        
        rate = (actual / expected * 100) if expected > 0 else 0
        
        return {
            "habit_id": habit.id,
            "habit_name": habit.name,
            "completion_rate": round(rate, 2),
            "completions": actual,
            "expected": expected,
        }
    
    return list(map(calc_rate, habits))