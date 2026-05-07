"""SQLite implementation of the :class:`StorageInterface` contract.

This module persists :class:`models.habit.Habit` objects to a SQLite
database file. It also installs explicit ``datetime`` adapters and
converters at import time, replacing the default adapters that Python
3.12 deprecated. Storing datetimes as ISO-8601 strings keeps the data
human-readable and survives sqlite tooling that does not understand
binary timestamps.
"""

import sqlite3
from datetime import datetime
from typing import List, Optional

from storage.interface import StorageInterface
from models.habit import Habit


def _adapt_datetime_iso(value: datetime) -> str:
    """Convert a :class:`datetime` into an ISO-8601 string for storage.

    Registered with :func:`sqlite3.register_adapter` so SQL parameters
    of type ``datetime`` are serialised consistently rather than relying
    on the default adapter (deprecated in Python 3.12).
    """
    return value.isoformat()


def _convert_datetime_iso(value: bytes) -> datetime:
    """Parse an ISO-8601 byte string from SQLite back into ``datetime``.

    Registered with :func:`sqlite3.register_converter` for the
    ``TIMESTAMP`` declared type so values come back as Python objects
    rather than raw strings when a query opts into type detection.
    """
    return datetime.fromisoformat(value.decode("utf-8"))


sqlite3.register_adapter(datetime, _adapt_datetime_iso)
sqlite3.register_converter("TIMESTAMP", _convert_datetime_iso)


def _coerce_datetime(value) -> datetime:
    """Return ``value`` as a :class:`datetime`.

    The SQLite type-detection converter normally returns ``datetime``
    instances directly, but legacy databases written before that
    converter was registered may still return ISO-8601 strings. This
    helper accepts either form so old data continues to load.
    """
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(value)


class SQLiteStorage(StorageInterface):
    """Concrete SQLite-backed implementation of :class:`StorageInterface`.

    A single long-lived :class:`sqlite3.Connection` is held for the
    lifetime of the instance with ``check_same_thread=False`` so the
    FastAPI worker threads can share it. ``row_factory`` is set to
    :class:`sqlite3.Row` so columns are accessible by name.
    """

    def __init__(self, db_path: str = "habits.db"):
        """Open (or create) the SQLite database at ``db_path``.

        Args:
            db_path: Filesystem path to the database file. Use
                ``":memory:"`` for an ephemeral in-process database.
        """
        self.db_path = db_path
        self.connection = sqlite3.connect(
            db_path,
            check_same_thread=False,
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        self.connection.row_factory = sqlite3.Row
        self._create_tables()
    
    def _create_tables(self) -> None:
        """Create the ``habits`` and ``completions`` tables if missing.

        Idempotent: safe to call on every startup. A foreign-key index
        on ``completions.habit_id`` is also created so loads scale
        linearly with the size of the parent habit, not the full table.
        """
        cursor = self.connection.cursor()
        
        # Habits table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS habits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                periodicity TEXT NOT NULL CHECK(periodicity IN ('daily', 'weekly')),
                created_at TIMESTAMP NOT NULL
            )
        """)
        
        # Completions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS completions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                habit_id INTEGER NOT NULL,
                completed_at TIMESTAMP NOT NULL,
                FOREIGN KEY (habit_id) REFERENCES habits (id) ON DELETE CASCADE
            )
        """)
        
        # Create index on habit_id for faster lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_completions_habit_id 
            ON completions(habit_id)
        """)
        
        self.connection.commit()
    
    def save_habit(self, habit: Habit) -> int:
        """Insert ``habit`` and any pre-existing completions.

        The provided :class:`Habit` is treated as new — a row is always
        inserted (no upsert). Any completions already attached to the
        in-memory object are persisted under the new habit ID.

        Args:
            habit: The habit to persist. The instance's ``id`` field is
                ignored on input; callers should write the returned ID
                back to the object if they continue to use it.

        Returns:
            The auto-generated primary key of the new ``habits`` row.
        """
        cursor = self.connection.cursor()
        
        cursor.execute("""
            INSERT INTO habits (name, description, periodicity, created_at)
            VALUES (?, ?, ?, ?)
        """, (habit.name, habit.description, habit.periodicity, habit.created_at))
        
        self.connection.commit()
        habit_id = cursor.lastrowid
        
        # Save any existing completions
        for completion in habit.completions:
            self.save_completion(habit_id, completion)
        
        return habit_id
    
    def load_habit(self, habit_id: int) -> Optional[Habit]:
        """Load a habit and all of its completions by primary key.

        Args:
            habit_id: The primary-key ID of the habit row to fetch.

        Returns:
            A reconstructed :class:`Habit` instance with populated
            completion history, or ``None`` when no row matches.
        """
        cursor = self.connection.cursor()

        cursor.execute("""
            SELECT id, name, description, periodicity, created_at
            FROM habits
            WHERE id = ?
        """, (habit_id,))

        row = cursor.fetchone()
        if not row:
            return None

        completions = self.load_completions(habit_id)

        return Habit(
            name=row["name"],
            description=row["description"],
            periodicity=row["periodicity"],
            habit_id=row["id"],
            created_at=_coerce_datetime(row["created_at"]),
            completions=completions,
        )

    def load_all_habits(self) -> List[Habit]:
        """Load every habit (with completions) ordered newest-first.

        Returns:
            A list of :class:`Habit` instances, ordered by descending
            ``created_at``. The list is empty if the database has no
            habits yet.
        """
        cursor = self.connection.cursor()

        cursor.execute("""
            SELECT id, name, description, periodicity, created_at
            FROM habits
            ORDER BY created_at DESC
        """)

        habits = []
        for row in cursor.fetchall():
            completions = self.load_completions(row["id"])
            habit = Habit(
                name=row["name"],
                description=row["description"],
                periodicity=row["periodicity"],
                habit_id=row["id"],
                created_at=_coerce_datetime(row["created_at"]),
                completions=completions,
            )
            habits.append(habit)

        return habits
    
    def update_habit(self, habit: Habit) -> bool:
        """Update mutable fields of an existing habit row.

        Only ``name``, ``description`` and ``periodicity`` are written
        back; ``created_at`` and the completion history are immutable
        through this call.

        Args:
            habit: The habit instance carrying updated values. Its
                ``id`` must be set to the row's primary key.

        Returns:
            ``True`` when a row was updated, ``False`` if ``habit.id``
            is ``None`` or matches no row.
        """
        if habit.id is None:
            return False
        
        cursor = self.connection.cursor()
        
        cursor.execute("""
            UPDATE habits
            SET name = ?, description = ?, periodicity = ?
            WHERE id = ?
        """, (habit.name, habit.description, habit.periodicity, habit.id))
        
        self.connection.commit()
        return cursor.rowcount > 0
    
    def delete_habit(self, habit_id: int) -> bool:
        """Delete a habit row.

        The ``ON DELETE CASCADE`` clause on ``completions.habit_id``
        removes the related completion rows automatically.

        Args:
            habit_id: Primary-key ID of the habit to delete.

        Returns:
            ``True`` if a row was deleted, ``False`` if the ID did not
            exist.
        """
        cursor = self.connection.cursor()
        
        cursor.execute("DELETE FROM habits WHERE id = ?", (habit_id,))
        self.connection.commit()
        
        return cursor.rowcount > 0
    
    def save_completion(self, habit_id: int, completion_date: datetime) -> bool:
        """Append a completion timestamp to a habit's history.

        Args:
            habit_id: Primary-key ID of the parent habit.
            completion_date: The instant at which the habit was
                completed. Stored as ISO-8601 via the registered
                adapter.

        Returns:
            ``True`` once the row has been committed.
        """
        cursor = self.connection.cursor()
        
        cursor.execute("""
            INSERT INTO completions (habit_id, completed_at)
            VALUES (?, ?)
        """, (habit_id, completion_date))
        
        self.connection.commit()
        return True
    
    def load_completions(self, habit_id: int) -> List[datetime]:
        """Load every completion timestamp recorded for a habit.

        Args:
            habit_id: The primary-key ID of the parent habit.

        Returns:
            A chronologically-ordered list of completion timestamps.
            Empty when the habit has no recorded completions.
        """
        cursor = self.connection.cursor()

        cursor.execute("""
            SELECT completed_at
            FROM completions
            WHERE habit_id = ?
            ORDER BY completed_at
        """, (habit_id,))

        return [
            _coerce_datetime(row["completed_at"])
            for row in cursor.fetchall()
        ]
    
    def close(self) -> None:
        """Close the underlying SQLite connection.

        Idempotent — safe to call multiple times. Subsequent operations
        on this instance will fail with a SQLite ``ProgrammingError``.
        """
        if self.connection:
            self.connection.close()

    def __del__(self):
        """Best-effort connection close on garbage collection.

        Production code should call :meth:`close` explicitly; relying
        on ``__del__`` is only a safety net for short-lived scripts.
        """
        try:
            self.close()
        except Exception:
            pass