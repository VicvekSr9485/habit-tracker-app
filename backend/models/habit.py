"""Core habit domain model and streak arithmetic.

This module deliberately contains no I/O. The :class:`Habit` class is a
plain Python object that the persistence layer hydrates, the analytics
layer reads, and the API layer wraps in Pydantic schemas. All time
arithmetic — period bucketing, streak counting, broken-state detection —
lives here so it is unit-testable without a database or HTTP client.

Two periodicities are supported:

``daily``
    A period is a single calendar day in local time, keyed by
    ``YYYY-MM-DD``.

``weekly``
    A period is an ISO week (Monday-start), keyed by ``YYYY-Www``.
    Sunday and the following Monday are therefore in *different*
    periods even though only one day apart.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any


class Habit:
    """A user-defined habit with its completion history.

    Instances are mutable; ``complete_task`` mutates the in-memory
    ``completions`` list and the storage layer persists those changes
    separately. Two completions that fall in the same period are
    deduplicated so the streak math doesn't double-count.

    Attributes:
        id: Database primary key, ``None`` for unsaved instances.
        name: Display name.
        description: Free-form description.
        periodicity: Either ``"daily"`` or ``"weekly"``.
        created_at: Instant the habit was first defined.
        completions: Chronologically-sorted list of completion times.
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
        """Record a completion, deduplicating within a period.

        Multiple calls within the same period (same calendar day for
        daily habits, same ISO week for weekly habits) are silently
        deduplicated and only the first is persisted in
        :attr:`completions`.

        Args:
            completion_date: Instant of completion. Defaults to
                :func:`datetime.now`.

        Returns:
            ``True`` when a new completion was recorded, ``False`` if
            the habit was already complete for this period.
        """
        if completion_date is None:
            completion_date = datetime.now()

        if not self._is_already_completed_for_period(completion_date):
            self.completions.append(completion_date)
            self.completions.sort()
            return True
        return False

    def _is_already_completed_for_period(self, date: datetime) -> bool:
        """Return ``True`` if ``date`` falls in an already-completed period."""
        period_key = self._get_period_key(date)
        return any(
            self._get_period_key(comp) == period_key
            for comp in self.completions
        )

    def _get_period_key(self, date: datetime) -> str:
        """Map ``date`` to the canonical key for its enclosing period.

        Daily habits use ``YYYY-MM-DD``; weekly habits use the ISO week
        number ``YYYY-Www``.
        """
        if self.periodicity == "daily":
            return date.strftime("%Y-%m-%d")
        else:  # weekly
            return f"{date.year}-W{date.isocalendar()[1]:02d}"

    def get_current_streak(self) -> int:
        """Count consecutive completed periods ending at "now".

        The streak is anchored to the *current* period: if the habit
        was not completed today (or this week) but was completed
        yesterday (or last week), the streak still counts — completing
        today simply extends it. A gap of one full empty period breaks
        the streak.

        Returns:
            The number of consecutive completed periods up to now,
            or ``0`` if there are no recent completions.
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
        """Return the longest historical run of consecutive periods.

        Walks every recorded completion in chronological order and
        tracks the longest run of adjacent periods. Unlike
        :meth:`get_current_streak`, this is a permanent achievement —
        it can be larger than the current streak when there has been a
        gap.

        Returns:
            The maximum number of consecutive completed periods, or
            ``0`` if the habit has never been completed.
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
        """Return ``True`` when the habit has missed a full period.

        For a habit with no completions, "broken" means we are past
        the first full period after :attr:`created_at`. For a habit
        with completions, it means we are past the period immediately
        following the most recent completion.

        Args:
            check_date: Reference instant; defaults to
                :func:`datetime.now`.

        Returns:
            ``True`` if the habit is currently considered broken.
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
        """Step ``date`` back by one period (one day or one week)."""
        if self.periodicity == "daily":
            return date - timedelta(days=1)
        else:
            return date - timedelta(weeks=1)

    def _get_next_period_date(self, date: datetime) -> datetime:
        """Step ``date`` forward by one period (one day or one week)."""
        if self.periodicity == "daily":
            return date + timedelta(days=1)
        else:
            return date + timedelta(weeks=1)

    def get_completion_dates(self) -> List[datetime]:
        """Return a sorted copy of every completion timestamp.

        The returned list is a copy, so callers may mutate it freely
        without affecting the habit's internal state.
        """
        return sorted(self.completions.copy())

    def to_dict(self) -> Dict[str, Any]:
        """Serialise the habit to a JSON-friendly dict.

        Datetimes are rendered as ISO-8601 strings and the dict
        includes computed fields (``current_streak``,
        ``longest_streak``) so callers can render summaries without
        re-instantiating the class.
        """
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
        """Reconstruct a :class:`Habit` from a :meth:`to_dict` payload.

        Datetime fields may be either ISO-8601 strings or already-parsed
        :class:`datetime` instances; both are accepted so the method
        round-trips with both JSON payloads and live objects.

        Args:
            data: Dict matching the schema produced by :meth:`to_dict`.

        Returns:
            A new :class:`Habit` instance with completions populated.
        """
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