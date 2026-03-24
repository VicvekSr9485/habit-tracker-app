"""FastAPI dependency injection."""

import os
from typing import Generator
from core.habit_manager import HabitManager
from storage.sqlite_storage import SQLiteStorage

# Global storage instance
_storage = None
_manager = None


def _resolve_db_path() -> str:
    """Resolve SQLite DB path from DATABASE_URL or fallback default."""
    database_url = os.getenv("DATABASE_URL", "sqlite:///habits.db")
    if database_url.startswith("sqlite:///"):
        return database_url.replace("sqlite:///", "", 1)
    return database_url


def get_storage() -> SQLiteStorage:
    """Get or create the storage instance."""
    global _storage
    if _storage is None:
        _storage = SQLiteStorage(_resolve_db_path())
    return _storage


def get_habit_manager() -> Generator[HabitManager, None, None]:
    """
    Dependency that provides a HabitManager instance.
    
    Yields:
        HabitManager instance
    """
    global _manager
    if _manager is None:
        storage = get_storage()
        _manager = HabitManager(storage)
    
    yield _manager