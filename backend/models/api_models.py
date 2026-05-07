"""Pydantic models for API request/response validation.

These schemas define the wire format for the FastAPI layer. They are
distinct from :class:`models.habit.Habit` (the domain model) and are
only used to validate inbound JSON and serialise outbound responses.

All models target Pydantic V2 and use :class:`pydantic.ConfigDict` for
configuration; the legacy nested ``class Config`` form is intentionally
avoided to keep the codebase free of deprecation warnings.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class HabitCreate(BaseModel):
    """Request body for ``POST /api/habits``.

    Fields are validated against length and pattern constraints. The
    ``name`` validator additionally trims surrounding whitespace and
    rejects entirely-blank values, since database CHECK constraints do
    not consider whitespace meaningful.
    """

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Human-readable habit name (1-100 chars, non-blank).",
    )
    description: str = Field(
        ...,
        max_length=500,
        description="Free-form description of the habit (max 500 chars).",
    )
    periodicity: str = Field(
        ...,
        pattern="^(daily|weekly)$",
        description="How often the habit should be completed.",
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Strip whitespace and reject blank-only names.

        Args:
            v: The raw ``name`` value supplied by the client.

        Returns:
            The stripped name.

        Raises:
            ValueError: If the value contains only whitespace.
        """
        if not v.strip():
            raise ValueError("Name cannot be empty or whitespace")
        return v.strip()

    @field_validator("periodicity")
    @classmethod
    def validate_periodicity(cls, v: str) -> str:
        """Enforce that ``periodicity`` is one of the supported values.

        Args:
            v: The raw ``periodicity`` value supplied by the client.

        Returns:
            The unchanged value when valid.

        Raises:
            ValueError: If the value is not ``"daily"`` or ``"weekly"``.
        """
        if v not in ["daily", "weekly"]:
            raise ValueError("Periodicity must be 'daily' or 'weekly'")
        return v


class HabitUpdate(BaseModel):
    """Request body for ``PUT /api/habits/{habit_id}``.

    All fields are optional so the client may submit a partial update;
    ``None`` values are skipped by the manager layer.
    """

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    periodicity: Optional[str] = Field(None, pattern="^(daily|weekly)$")


class HabitResponse(BaseModel):
    """Response schema returned by every habit-shaped endpoint.

    Includes computed fields (``current_streak``, ``longest_streak``,
    ``completion_count``, ``is_broken``) that the frontend renders
    directly so it does not need to recompute streak logic client-side.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str
    periodicity: str
    created_at: datetime
    current_streak: int
    longest_streak: int
    completion_count: int
    is_broken: bool


class CompletionCreate(BaseModel):
    """Request body for ``POST /api/habits/{habit_id}/complete``.

    Clients may omit ``completed_at`` to default to the server's
    current time.
    """

    completed_at: Optional[datetime] = None


class AnalyticsResponse(BaseModel):
    """Response schema for ``GET /api/analytics/summary``.

    ``longest_streak_habit`` may be ``None`` when no habits exist.
    ``average_streak`` is the mean of every habit's *current* streak.
    """

    total_habits: int
    daily_habits: int
    weekly_habits: int
    longest_streak_habit: Optional[str] = None
    longest_streak_days: int = 0
    total_completions: int
    average_streak: float


class HabitListResponse(BaseModel):
    """Response schema for ``GET /api/habits``.

    ``total`` mirrors ``len(habits)``; it is sent explicitly so clients
    can render counts without inspecting the array.
    """

    habits: List[HabitResponse]
    total: int