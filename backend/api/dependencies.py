"""FastAPI dependency factories.

Both the storage and the manager are process-singletons. They are
created lazily on first request so unit tests can replace them via
:meth:`fastapi.FastAPI.dependency_overrides` without ever touching the
real database file.
"""

import os
from typing import Generator

from core.habit_manager import HabitManager
from storage.sqlite_storage import SQLiteStorage

_storage: SQLiteStorage | None = None
_manager: HabitManager | None = None


def _resolve_db_path() -> str:
    """Return the SQLite file path from ``DATABASE_URL``.

    Accepts the ``sqlite:///<path>`` URL form to mirror SQLAlchemy
    conventions. Falls back to ``"habits.db"`` in the working directory
    when the variable is unset.
    """
    database_url = os.getenv("DATABASE_URL", "sqlite:///habits.db")
    if database_url.startswith("sqlite:///"):
        return database_url.replace("sqlite:///", "", 1)
    return database_url


def get_storage() -> SQLiteStorage:
    """Return the process-wide :class:`SQLiteStorage` singleton.

    Creates the instance on first call. Subsequent calls return the
    same object so connections are reused for the lifetime of the
    process.
    """
    global _storage
    if _storage is None:
        _storage = SQLiteStorage(_resolve_db_path())
    return _storage


def get_habit_manager() -> Generator[HabitManager, None, None]:
    """FastAPI dependency that yields the singleton :class:`HabitManager`.

    Yields:
        The :class:`HabitManager` bound to the singleton storage.
    """
    global _manager
    if _manager is None:
        storage = get_storage()
        _manager = HabitManager(storage)

    yield _manager