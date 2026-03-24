"""SQLite implementation of storage interface."""

import sqlite3
from datetime import datetime
from typing import List, Optional
from pathlib import Path

from storage.interface import StorageInterface
from models.habit import Habit


class SQLiteStorage(StorageInterface):
    """SQLite database storage implementation."""
    
    def __init__(self, db_path: str = "habits.db"):
        """
        Initialize SQLite storage.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self.connection = sqlite3.connect(db_path, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self._create_tables()
    
    def _create_tables(self) -> None:
        """Create database tables if they don't exist."""
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
        """Save a new habit to the database."""
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
        """Load a habit by ID from the database."""
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
            created_at=datetime.fromisoformat(row["created_at"]),
            completions=completions,
        )
    
    def load_all_habits(self) -> List[Habit]:
        """Load all habits from the database."""
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
                created_at=datetime.fromisoformat(row["created_at"]),
                completions=completions,
            )
            habits.append(habit)
        
        return habits
    
    def update_habit(self, habit: Habit) -> bool:
        """Update an existing habit in the database."""
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
        """Delete a habit from the database."""
        cursor = self.connection.cursor()
        
        cursor.execute("DELETE FROM habits WHERE id = ?", (habit_id,))
        self.connection.commit()
        
        return cursor.rowcount > 0
    
    def save_completion(self, habit_id: int, completion_date: datetime) -> bool:
        """Save a completion record for a habit."""
        cursor = self.connection.cursor()
        
        cursor.execute("""
            INSERT INTO completions (habit_id, completed_at)
            VALUES (?, ?)
        """, (habit_id, completion_date))
        
        self.connection.commit()
        return True
    
    def load_completions(self, habit_id: int) -> List[datetime]:
        """Load all completion dates for a habit."""
        cursor = self.connection.cursor()
        
        cursor.execute("""
            SELECT completed_at
            FROM completions
            WHERE habit_id = ?
            ORDER BY completed_at
        """, (habit_id,))
        
        return [
            datetime.fromisoformat(row["completed_at"])
            for row in cursor.fetchall()
        ]
    
    def close(self) -> None:
        """Close the database connection."""
        if self.connection:
            self.connection.close()
    
    def __del__(self):
        """Ensure connection is closed when object is destroyed."""
        self.close()