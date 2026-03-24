"""Habit Manager - coordinates habit operations."""

from datetime import datetime
from typing import List, Optional

from models.habit import Habit
from storage.interface import StorageInterface


class HabitManager:
    """
    Manages habit operations and coordinates between storage and domain logic.
    """
    
    def __init__(self, storage: StorageInterface):
        """
        Initialize the HabitManager.
        
        Args:
            storage: Storage implementation to use for persistence
        """
        self.storage = storage
        self._habits_cache: dict[int, Habit] = {}
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
        """
        Create a new habit.
        
        Args:
            name: Name of the habit
            description: Description of the habit
            periodicity: How often to track ('daily' or 'weekly')
        
        Returns:
            The created Habit instance
        
        Raises:
            ValueError: If parameters are invalid
        """
        habit = Habit(
            name=name,
            description=description,
            periodicity=periodicity
        )
        
        habit_id = self.storage.save_habit(habit)
        habit.id = habit_id
        self._habits_cache[habit_id] = habit
        
        return habit
    
    def get_habit(self, habit_id: int) -> Optional[Habit]:
        """
        Get a habit by ID.
        
        Args:
            habit_id: The ID of the habit to retrieve
        
        Returns:
            The Habit if found, None otherwise
        """
        # Try cache first
        if habit_id in self._habits_cache:
            return self._habits_cache[habit_id]
        
        # Load from storage
        habit = self.storage.load_habit(habit_id)
        if habit:
            self._habits_cache[habit_id] = habit
        
        return habit
    
    def get_all_habits(self) -> List[Habit]:
        """
        Get all habits.
        
        Returns:
            List of all habits
        """
        return list(self._habits_cache.values())
    
    def update_habit(
        self,
        habit_id: int,
        name: str | None = None,
        description: str | None = None,
        periodicity: str | None = None
    ) -> Optional[Habit]:
        """
        Update an existing habit.
        
        Args:
            habit_id: ID of the habit to update
            name: New name (optional)
            description: New description (optional)
            periodicity: New periodicity (optional)
        
        Returns:
            Updated Habit if successful, None otherwise
        """
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
        """
        Delete a habit.
        
        Args:
            habit_id: ID of the habit to delete
        
        Returns:
            True if deletion was successful
        """
        success = self.storage.delete_habit(habit_id)
        if success and habit_id in self._habits_cache:
            del self._habits_cache[habit_id]
        return success
    
    def complete_habit(
        self,
        habit_id: int,
        completion_date: datetime | None = None
    ) -> bool:
        """
        Mark a habit as completed.
        
        Args:
            habit_id: ID of the habit to complete
            completion_date: Date/time of completion (defaults to now)
        
        Returns:
            True if completion was recorded successfully
        """
        habit = self.get_habit(habit_id)
        if not habit:
            return False
        
        if completion_date is None:
            completion_date = datetime.now()
        
        # Add completion to habit
        success = habit.complete_task(completion_date)
        
        # Persist to storage
        if success:
            self.storage.save_completion(habit_id, completion_date)
        
        return success
    
    def get_habits_by_periodicity(self, periodicity: str) -> List[Habit]:
        """
        Get all habits with a specific periodicity.
        
        Args:
            periodicity: The periodicity to filter by ('daily' or 'weekly')
        
        Returns:
            List of habits matching the periodicity
        """
        return [
            habit for habit in self._habits_cache.values()
            if habit.periodicity == periodicity
        ]