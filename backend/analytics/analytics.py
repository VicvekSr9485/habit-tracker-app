"""Functional analytics module for habit data analysis.

Each function in this module is a pure, side-effect-free transformation
over a list of :class:`Habit` objects. They are deliberately written
with ``map``/``filter``/``reduce`` to illustrate a functional style
appropriate for the IU "Object-Oriented and Functional Programming with
Python" assignment, and to make composition with the FastAPI layer
trivial: the API simply hands the in-memory list of habits to a
function and serialises the return value.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple, Optional
from functools import reduce

from models.habit import Habit


def get_all_habits(habits: List[Habit]) -> List[Dict[str, Any]]:
    """Project habits to a lightweight summary form.

    Args:
        habits: Habits to summarise.

    Returns:
        One dict per habit containing ``id``, ``name``, ``periodicity``,
        ``current_streak`` and an ISO-8601 ``created_at``. The list
        preserves the order of ``habits``.
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
    """Return only the habits whose periodicity matches.

    Args:
        habits: Habits to filter.
        periodicity: ``"daily"`` or ``"weekly"``.

    Returns:
        A new list containing the matching habits, preserving order.
    """
    return list(filter(lambda h: h.periodicity == periodicity, habits))


def get_longest_streak_all(habits: List[Habit]) -> Tuple[Optional[str], int]:
    """Find the longest streak achieved across every habit.

    Args:
        habits: Habits to inspect.

    Returns:
        A tuple ``(habit_name, streak_length)``. When the list is empty
        — or every habit has a zero streak — returns ``(None, 0)``.
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
    """Return the longest historical streak for a single habit.

    A thin wrapper over :meth:`Habit.get_longest_streak` retained for
    symmetry with the other module-level analytics functions.

    Args:
        habit: The habit to inspect.

    Returns:
        The longest streak length, or ``0`` if the habit has no
        completions.
    """
    return habit.get_longest_streak()


def get_struggling_habits(
    habits: List[Habit],
    period_days: int = 30
) -> List[Dict[str, Any]]:
    """Identify habits with a completion rate below 50% over a window.

    "Expected" completions are estimated from the periodicity and the
    number of days the habit has existed within the lookback window
    (capped to the window length). The result is sorted from worst to
    best so the most-neglected habits surface first.

    Args:
        habits: Habits to evaluate.
        period_days: Lookback window in days (default ``30``).

    Returns:
        A list of dicts, one per struggling habit, with keys ``id``,
        ``name``, ``periodicity``, ``completion_rate`` (percentage,
        rounded to 2 d.p.), ``expected`` and ``actual``.
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
    """Aggregate top-level metrics for the analytics dashboard.

    Args:
        habits: Habits to summarise.

    Returns:
        A dict with keys ``total_habits``, ``daily_habits``,
        ``weekly_habits``, ``longest_streak_habit``,
        ``longest_streak_days``, ``total_completions`` and
        ``average_streak`` (mean of *current* streaks). When ``habits``
        is empty, every numeric key is ``0`` and ``longest_streak_habit``
        is ``None``.
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
    """Compute per-habit completion rates over a lookback window.

    Args:
        habits: Habits to evaluate.
        days: Lookback window in days (default ``30``).

    Returns:
        A list of dicts (one per habit) with keys ``habit_id``,
        ``habit_name``, ``completion_rate`` (percentage rounded to 2
        d.p.), ``completions`` and ``expected``. Order matches the
        input list.
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