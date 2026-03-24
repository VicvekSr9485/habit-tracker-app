"""Sample data generator for testing and demonstration."""

from datetime import datetime, timedelta
from typing import List
import random

from models.habit import Habit
from storage.interface import StorageInterface


def generate_sample_habits() -> List[Habit]:
    """
    Generate 5 predefined habits with 4 weeks of sample data.
    
    Returns:
        List of Habit objects with completion history
    """
    base_date = datetime.now() - timedelta(days=28)
    
    # Habit 1: Morning Exercise (daily, high consistency - 90%)
    exercise = Habit(
        name="Morning Exercise",
        description="30 minutes of physical activity",
        periodicity="daily",
        created_at=base_date
    )
    
    # Habit 2: Read for 30 Minutes (daily, moderate consistency - 70%)
    reading = Habit(
        name="Read for 30 Minutes",
        description="Read books or articles",
        periodicity="daily",
        created_at=base_date
    )
    
    # Habit 3: Meditate (daily, building streak - 60%)
    meditation = Habit(
        name="Meditate",
        description="10 minutes of mindfulness meditation",
        periodicity="daily",
        created_at=base_date
    )
    
    # Habit 4: Weekly Grocery Shopping (weekly, consistent)
    groceries = Habit(
        name="Weekly Grocery Shopping",
        description="Buy groceries for the week",
        periodicity="weekly",
        created_at=base_date
    )
    
    # Habit 5: Clean Home Office (weekly, some gaps)
    cleaning = Habit(
        name="Clean Home Office",
        description="Organize and clean workspace",
        periodicity="weekly",
        created_at=base_date
    )
    
    # Generate completions for daily habits
    for day in range(28):
        completion_date = base_date + timedelta(days=day)
        
        # Exercise: 90% completion rate
        if random.random() < 0.90:
            exercise.complete_task(
                completion_date.replace(
                    hour=7,
                    minute=random.randint(0, 59)
                )
            )
        
        # Reading: 70% completion rate
        if random.random() < 0.70:
            reading.complete_task(
                completion_date.replace(
                    hour=20,
                    minute=random.randint(0, 59)
                )
            )
        
        # Meditation: 60% completion rate, improving over time
        completion_probability = 0.50 + (day / 28) * 0.30
        if random.random() < completion_probability:
            meditation.complete_task(
                completion_date.replace(
                    hour=6,
                    minute=random.randint(0, 59)
                )
            )
    
    # Generate completions for weekly habits
    for week in range(4):
        week_date = base_date + timedelta(weeks=week)
        
        # Groceries: Complete every week
        groceries.complete_task(
            week_date.replace(
                hour=10,
                minute=random.randint(0, 59)
            )
        )
        
        # Cleaning: Skip week 2
        if week != 1:
            cleaning.complete_task(
                week_date.replace(
                    hour=14,
                    minute=random.randint(0, 59)
                )
            )
    
    return [exercise, reading, meditation, groceries, cleaning]


def load_sample_data(storage: StorageInterface) -> None:
    """
    Load sample habits into storage.
    
    Args:
        storage: Storage implementation to save habits to
    """
    habits = generate_sample_habits()
    
    for habit in habits:
        habit_id = storage.save_habit(habit)
        print(f"Loaded sample habit: {habit.name} (ID: {habit_id})")