"""Habit Manager — coordinates domain logic, the in-memory cache and storage.

The :class:`HabitManager` is the single entry point used by both the FastAPI
and CLI front-ends. It keeps habits in an in-memory dictionary that mirrors
the database, and serialises mutating operations behind a re-entrant lock so
concurrent completion calls from FastAPI's worker threads cannot corrupt
either the cache or the underlying SQLite connection.
"""

import threading
from datetime import datetime
from typing import List, Optional

from models.habit import Habit
from storage.interface import StorageInterface


class HabitManager:
    """Coordinates habit operations between storage and the domain model.

    A single re-entrant lock (:attr:`_lock`) guards every mutating call.
    SQLite connections opened with ``check_same_thread=False`` are still
    not safe to share between threads without external synchronisation;
    this lock provides that synchronisation and also ensures the
    ``check + write`` step inside :meth:`complete_habit` is atomic.
    """

    def __init__(self, storage: StorageInterface):
        """Wire the manager to a storage implementation.

        Args:
            storage: The storage backend used for persistence. The
                manager loads every existing habit into memory at
                construction time so subsequent reads are O(1).
        """
        self.storage = storage
        self._habits_cache: dict[int, Habit] = {}
        self._lock = threading.RLock()
        self._load_all_habits()
    
    def _load_all_habits(self) -> None:
        """Load all habits from storage into cache."""
        habits = self.storage.load_all_habits()
        self._habits_cache = {habit.id: habit for habit in habits if habit.id}
    
    def create_habit(
        self,
        name: str,
        description: str,
        periodicity: str
    ) -> Habit:
        """Create, persist and cache a new habit.

        Args:
            name: Display name of the habit.
            description: Free-form description of the habit.
            periodicity: ``"daily"`` or ``"weekly"``.

        Returns:
            The freshly-persisted :class:`Habit`, with ``id`` populated
            from the database.

        Raises:
            ValueError: When ``periodicity`` is not a valid value.
        """
        with self._lock:
            habit = Habit(
                name=name,
                description=description,
                periodicity=periodicity,
            )

            habit_id = self.storage.save_habit(habit)
            habit.id = habit_id
            self._habits_cache[habit_id] = habit

            return habit

    def get_habit(self, habit_id: int) -> Optional[Habit]:
        """Return a habit by ID, falling back to storage on a cache miss.

        Args:
            habit_id: Primary-key ID of the habit to retrieve.

        Returns:
            The :class:`Habit` if it exists in the cache or storage,
            otherwise ``None``.
        """
        with self._lock:
            if habit_id in self._habits_cache:
                return self._habits_cache[habit_id]

            habit = self.storage.load_habit(habit_id)
            if habit:
                self._habits_cache[habit_id] = habit

            return habit

    def get_all_habits(self) -> List[Habit]:
        """Return every cached habit.

        The cache is populated at construction time and kept in sync by
        every mutating method, so this never falls back to the database.

        Returns:
            A list snapshot of the cache (callers may iterate freely).
        """
        with self._lock:
            return list(self._habits_cache.values())

    def update_habit(
        self,
        habit_id: int,
        name: str | None = None,
        description: str | None = None,
        periodicity: str | None = None
    ) -> Optional[Habit]:
        """Apply a partial update to a habit.

        Any argument left at its default of ``None`` is ignored, so
        callers can mutate one field at a time without having to read
        the others first.

        Args:
            habit_id: Primary-key ID of the habit to update.
            name: New name, or ``None`` to leave unchanged.
            description: New description, or ``None`` to leave unchanged.
            periodicity: New periodicity, or ``None`` to leave unchanged.

        Returns:
            The updated :class:`Habit` instance, or ``None`` if the ID
            does not exist.

        Raises:
            ValueError: If ``periodicity`` is provided and not valid.
        """
        with self._lock:
            habit = self.get_habit(habit_id)
            if not habit:
                return None

            if name is not None:
                habit.name = name
            if description is not None:
                habit.description = description
            if periodicity is not None:
                if periodicity not in Habit.VALID_PERIODICITIES:
                    raise ValueError(f"Invalid periodicity: {periodicity}")
                habit.periodicity = periodicity

            self.storage.update_habit(habit)
            return habit

    def delete_habit(self, habit_id: int) -> bool:
        """Delete a habit and evict it from the cache.

        Args:
            habit_id: Primary-key ID of the habit to delete.

        Returns:
            ``True`` when the row was deleted, ``False`` if no row
            matched the ID.
        """
        with self._lock:
            success = self.storage.delete_habit(habit_id)
            if success and habit_id in self._habits_cache:
                del self._habits_cache[habit_id]
            return success

    def complete_habit(
        self,
        habit_id: int,
        completion_date: datetime | None = None
    ) -> bool:
        """Record a completion for a habit.

        The whole *check + write* sequence runs under :attr:`_lock`, so
        even if many threads call this concurrently for the same period
        only one persisted row is created and at most one call returns
        ``True``.

        Args:
            habit_id: Primary-key ID of the habit to complete.
            completion_date: Instant of completion. Defaults to now.

        Returns:
            ``True`` if a new completion was recorded, ``False`` if the
            habit doesn't exist or was already completed for this period.
        """
        with self._lock:
            habit = self.get_habit(habit_id)
            if not habit:
                return False

            if completion_date is None:
                completion_date = datetime.now()

            success = habit.complete_task(completion_date)

            if success:
                self.storage.save_completion(habit_id, completion_date)

            return success

    def get_habits_by_periodicity(self, periodicity: str) -> List[Habit]:
        """Return cached habits matching a given periodicity.

        Args:
            periodicity: ``"daily"`` or ``"weekly"``.

        Returns:
            The subset of habits whose ``periodicity`` field matches.
        """
        with self._lock:
            return [
                habit for habit in self._habits_cache.values()
                if habit.periodicity == periodicity
            ]