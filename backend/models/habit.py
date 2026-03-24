"""Core Habit domain model."""

from datetime import datetime, timedelta
from typing import List, Dict, Any


class Habit:
    """
    Represents a habit that a user wants to track.
    
    A habit has a name, description, periodicity (daily or weekly),
    and tracks completion dates to calculate streaks.
    """
    
    VALID_PERIODICITIES = ["daily", "weekly"]
    
    def __init__(
        self,
        name: str,
        description: str,
        periodicity: str,
        habit_id: int | None = None,
        created_at: datetime | None = None,
        completions: List[datetime] | None = None,
    ):
        """
        Initialize a new Habit.
        
        Args:
            name: The name of the habit
            description: A detailed description of the habit
            periodicity: How often the habit should be completed ('daily' or 'weekly')
            habit_id: Optional ID for the habit
            created_at: Optional creation timestamp
            completions: Optional list of completion timestamps
        
        Raises:
            ValueError: If periodicity is not 'daily' or 'weekly'
        """
        if periodicity not in self.VALID_PERIODICITIES:
            raise ValueError(
                f"Invalid periodicity: '{periodicity}'. "
                f"Expected 'daily' or 'weekly'"
            )
        
        self.id = habit_id
        self.name = name
        self.description = description
        self.periodicity = periodicity
        self.created_at = created_at or datetime.now()
        self.completions: List[datetime] = completions or []
    
    def complete_task(self, completion_date: datetime | None = None) -> bool:
        """
        Mark the habit as completed for a given date.
        
        Args:
            completion_date: The date/time of completion (defaults to now)
        
        Returns:
            True if the completion was recorded successfully
        """
        if completion_date is None:
            completion_date = datetime.now()
        
        # Avoid duplicate completions for the same period
        if not self._is_already_completed_for_period(completion_date):
            self.completions.append(completion_date)
            self.completions.sort()
            return True
        return False
    
    def _is_already_completed_for_period(self, date: datetime) -> bool:
        """Check if habit is already completed for the given period."""
        period_key = self._get_period_key(date)
        return any(
            self._get_period_key(comp) == period_key
            for comp in self.completions
        )
    
    def _get_period_key(self, date: datetime) -> str:
        """Get a unique key for the period containing the given date."""
        if self.periodicity == "daily":
            return date.strftime("%Y-%m-%d")
        else:  # weekly
            # ISO week format: year-week_number
            return f"{date.year}-W{date.isocalendar()[1]:02d}"
    
    def get_current_streak(self) -> int:
        """
        Calculate the current streak of consecutive completions.
        
        Returns:
            The number of consecutive periods with completions up to now
        """
        if not self.completions:
            return 0
        
        now = datetime.now()
        current_period = self._get_period_key(now)
        previous_period = self._get_period_key(
            self._get_previous_period_date(now)
        )
        
        # Sort completions in reverse order
        sorted_completions = sorted(self.completions, reverse=True)
        
        # Check if current or previous period has completion
        latest_period = self._get_period_key(sorted_completions[0])
        if latest_period != current_period and latest_period != previous_period:
            return 0
        
        streak = 0
        expected_date = now
        
        for completion in sorted_completions:
            completion_period = self._get_period_key(completion)
            expected_period = self._get_period_key(expected_date)
            
            if completion_period == expected_period:
                streak += 1
                expected_date = self._get_previous_period_date(expected_date)
            elif streak > 0:
                # Gap found, stop counting
                break
        
        return streak
    
    def get_longest_streak(self) -> int:
        """
        Calculate the longest streak ever achieved for this habit.
        
        Returns:
            The maximum number of consecutive periods with completions
        """
        if not self.completions:
            return 0
        
        sorted_completions = sorted(self.completions)
        max_streak = 1
        current_streak = 1
        
        for i in range(1, len(sorted_completions)):
            current_period = self._get_period_key(sorted_completions[i])
            previous_completion = sorted_completions[i - 1]
            expected_date = self._get_next_period_date(previous_completion)
            expected_period = self._get_period_key(expected_date)
            
            if current_period == expected_period or current_period == self._get_period_key(previous_completion):
                current_streak += 1 if current_period == expected_period else 0
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 1
        
        return max_streak
    
    def is_broken(self, check_date: datetime | None = None) -> bool:
        """
        Check if the habit is currently broken (missed the required period).
        
        Args:
            check_date: The date to check against (defaults to now)
        
        Returns:
            True if the habit has been broken
        """
        if check_date is None:
            check_date = datetime.now()
        
        if not self.completions:
            # Check if we're past the first period after creation
            first_period_end = self._get_next_period_date(self.created_at)
            return check_date > first_period_end
        
        latest_completion = max(self.completions)
        next_required_period = self._get_next_period_date(latest_completion)
        
        return check_date > next_required_period
    
    def _get_previous_period_date(self, date: datetime) -> datetime:
        """Get the start date of the previous period."""
        if self.periodicity == "daily":
            return date - timedelta(days=1)
        else:  # weekly
            return date - timedelta(weeks=1)
    
    def _get_next_period_date(self, date: datetime) -> datetime:
        """Get the start date of the next period."""
        if self.periodicity == "daily":
            return date + timedelta(days=1)
        else:  # weekly
            return date + timedelta(weeks=1)
    
    def get_completion_dates(self) -> List[datetime]:
        """Get all completion dates for this habit."""
        return sorted(self.completions.copy())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the habit to a dictionary representation."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "periodicity": self.periodicity,
            "created_at": self.created_at.isoformat(),
            "completions": [comp.isoformat() for comp in self.completions],
            "current_streak": self.get_current_streak(),
            "longest_streak": self.get_longest_streak(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Habit":
        """Create a Habit instance from a dictionary."""
        return cls(
            name=data["name"],
            description=data["description"],
            periodicity=data["periodicity"],
            habit_id=data.get("id"),
            created_at=datetime.fromisoformat(data["created_at"])
            if isinstance(data["created_at"], str)
            else data["created_at"],
            completions=[
                datetime.fromisoformat(comp) if isinstance(comp, str) else comp
                for comp in data.get("completions", [])
            ],
        )
    
    def __repr__(self) -> str:
        return (
            f"Habit(id={self.id}, name='{self.name}', "
            f"periodicity='{self.periodicity}', "
            f"streak={self.get_current_streak()})"
        )