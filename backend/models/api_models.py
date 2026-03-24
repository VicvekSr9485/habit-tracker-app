"""Pydantic models for API request/response validation."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class HabitCreate(BaseModel):
    """Model for creating a new habit."""
    
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., max_length=500)
    periodicity: str = Field(..., pattern="^(daily|weekly)$")
    
    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Ensure name is not just whitespace."""
        if not v.strip():
            raise ValueError("Name cannot be empty or whitespace")
        return v.strip()
    
    @field_validator("periodicity")
    @classmethod
    def validate_periodicity(cls, v: str) -> str:
        """Ensure periodicity is valid."""
        if v not in ["daily", "weekly"]:
            raise ValueError("Periodicity must be 'daily' or 'weekly'")
        return v


class HabitUpdate(BaseModel):
    """Model for updating an existing habit."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    periodicity: Optional[str] = Field(None, pattern="^(daily|weekly)$")


class HabitResponse(BaseModel):
    """Model for habit data in API responses."""
    
    id: int
    name: str
    description: str
    periodicity: str
    created_at: datetime
    current_streak: int
    longest_streak: int
    completion_count: int
    is_broken: bool
    
    class Config:
        from_attributes = True


class CompletionCreate(BaseModel):
    """Model for creating a habit completion."""
    
    completed_at: Optional[datetime] = None


class AnalyticsResponse(BaseModel):
    """Model for analytics summary data."""
    
    total_habits: int
    daily_habits: int
    weekly_habits: int
    longest_streak_habit: Optional[str] = None
    longest_streak_days: int = 0
    total_completions: int
    average_streak: float


class HabitListResponse(BaseModel):
    """Model for list of habits."""
    
    habits: List[HabitResponse]
    total: int