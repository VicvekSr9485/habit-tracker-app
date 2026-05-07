"""Abstract storage contract.

Concrete persistence layers must implement :class:`StorageInterface`.
The current production backend is :class:`storage.sqlite_storage.SQLiteStorage`
but the interface is deliberately small so a Postgres or in-memory
implementation can drop in without touching the manager or API layers.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional

from models.habit import Habit


class StorageInterface(ABC):
    """Persistence contract used by :class:`HabitManager`.

    Implementations are expected to be safe to share between threads
    when used through :class:`HabitManager` (which provides its own
    locking) — they do not need to be lock-free on their own.
    """
    
    @abstractmethod
    def save_habit(self, habit: Habit) -> int:
        """
        Save a new habit to storage.
        
        Args:
            habit: The habit to save
        
        Returns:
            The ID of the saved habit
        """
        pass
    
    @abstractmethod
    def load_habit(self, habit_id: int) -> Optional[Habit]:
        """
        Load a habit by its ID.
        
        Args:
            habit_id: The ID of the habit to load
        
        Returns:
            The habit if found, None otherwise
        """
        pass
    
    @abstractmethod
    def load_all_habits(self) -> List[Habit]:
        """
        Load all habits from storage.
        
        Returns:
            List of all habits
        """
        pass
    
    @abstractmethod
    def update_habit(self, habit: Habit) -> bool:
        """
        Update an existing habit.
        
        Args:
            habit: The habit with updated data
        
        Returns:
            True if update was successful
        """
        pass
    
    @abstractmethod
    def delete_habit(self, habit_id: int) -> bool:
        """
        Delete a habit by its ID.
        
        Args:
            habit_id: The ID of the habit to delete
        
        Returns:
            True if deletion was successful
        """
        pass
    
    @abstractmethod
    def save_completion(self, habit_id: int, completion_date: datetime) -> bool:
        """
        Save a completion record for a habit.
        
        Args:
            habit_id: The ID of the habit
            completion_date: The date/time of completion
        
        Returns:
            True if save was successful
        """
        pass
    
    @abstractmethod
    def load_completions(self, habit_id: int) -> List[datetime]:
        """
        Load all completion dates for a habit.
        
        Args:
            habit_id: The ID of the habit
        
        Returns:
            List of completion dates
        """
        pass
    
    @abstractmethod
    def close(self) -> None:
        """Close the storage connection."""
        pass