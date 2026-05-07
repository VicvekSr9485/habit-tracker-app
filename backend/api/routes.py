"""FastAPI route definitions for the habit tracker API.

Routes are mounted under the ``/api`` prefix and grouped under the
``"habits"`` tag for OpenAPI. Each handler keeps its body small —
validation lives in the Pydantic schemas (:mod:`models.api_models`),
business logic in :mod:`core.habit_manager`, and pure analytics in
:mod:`analytics.analytics` — so the routes are essentially adapters.
"""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from core.habit_manager import HabitManager
from models.api_models import (
    HabitCreate,
    HabitUpdate,
    HabitResponse,
    CompletionCreate,
    AnalyticsResponse,
    HabitListResponse,
)
from analytics import analytics
from api.dependencies import get_habit_manager

router = APIRouter(prefix="/api", tags=["habits"])


# Habit CRUD endpoints

@router.post("/habits", response_model=HabitResponse, status_code=201)
async def create_habit(
    habit_data: HabitCreate,
    manager: HabitManager = Depends(get_habit_manager)
):
    """Create a habit.

    Validates the request body against :class:`HabitCreate`, persists
    a new habit and returns its full :class:`HabitResponse`. Returns
    HTTP 400 when the manager raises :class:`ValueError` (e.g. an
    invalid periodicity that slipped past the schema).
    """
    try:
        habit = manager.create_habit(
            name=habit_data.name,
            description=habit_data.description,
            periodicity=habit_data.periodicity
        )
        
        return HabitResponse(
            id=habit.id,
            name=habit.name,
            description=habit.description,
            periodicity=habit.periodicity,
            created_at=habit.created_at,
            current_streak=habit.get_current_streak(),
            longest_streak=habit.get_longest_streak(),
            completion_count=len(habit.completions),
            is_broken=habit.is_broken(),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/habits", response_model=HabitListResponse)
async def get_habits(
    periodicity: Optional[str] = Query(None, pattern="^(daily|weekly)$"),
    manager: HabitManager = Depends(get_habit_manager)
):
    """List habits.

    When ``periodicity`` is supplied (``daily`` or ``weekly``) the list
    is filtered server-side; otherwise every habit is returned in the
    default newest-first order.
    """
    if periodicity:
        habits = manager.get_habits_by_periodicity(periodicity)
    else:
        habits = manager.get_all_habits()
    
    habit_responses = [
        HabitResponse(
            id=habit.id,
            name=habit.name,
            description=habit.description,
            periodicity=habit.periodicity,
            created_at=habit.created_at,
            current_streak=habit.get_current_streak(),
            longest_streak=habit.get_longest_streak(),
            completion_count=len(habit.completions),
            is_broken=habit.is_broken(),
        )
        for habit in habits
    ]
    
    return HabitListResponse(habits=habit_responses, total=len(habit_responses))


@router.get("/habits/{habit_id}", response_model=HabitResponse)
async def get_habit(
    habit_id: int,
    manager: HabitManager = Depends(get_habit_manager)
):
    """Fetch one habit by ID, returning HTTP 404 when not found."""
    habit = manager.get_habit(habit_id)
    
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")
    
    return HabitResponse(
        id=habit.id,
        name=habit.name,
        description=habit.description,
        periodicity=habit.periodicity,
        created_at=habit.created_at,
        current_streak=habit.get_current_streak(),
        longest_streak=habit.get_longest_streak(),
        completion_count=len(habit.completions),
        is_broken=habit.is_broken(),
    )


@router.put("/habits/{habit_id}", response_model=HabitResponse)
async def update_habit(
    habit_id: int,
    habit_data: HabitUpdate,
    manager: HabitManager = Depends(get_habit_manager)
):
    """Apply a partial update to a habit.

    Any field omitted from the body is left unchanged. Returns 404
    when the habit does not exist and 400 on validation errors.
    """
    try:
        habit = manager.update_habit(
            habit_id=habit_id,
            name=habit_data.name,
            description=habit_data.description,
            periodicity=habit_data.periodicity
        )
        
        if not habit:
            raise HTTPException(status_code=404, detail="Habit not found")
        
        return HabitResponse(
            id=habit.id,
            name=habit.name,
            description=habit.description,
            periodicity=habit.periodicity,
            created_at=habit.created_at,
            current_streak=habit.get_current_streak(),
            longest_streak=habit.get_longest_streak(),
            completion_count=len(habit.completions),
            is_broken=habit.is_broken(),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/habits/{habit_id}", status_code=204)
async def delete_habit(
    habit_id: int,
    manager: HabitManager = Depends(get_habit_manager)
):
    """Delete a habit and its completion history.

    Cascading delete on the SQLite layer also removes any related
    completion rows. Returns 204 on success, 404 if the ID is unknown.
    """
    success = manager.delete_habit(habit_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Habit not found")
    
    return None


# Completion endpoints

@router.post("/habits/{habit_id}/complete", response_model=HabitResponse)
async def complete_habit(
    habit_id: int,
    completion_data: CompletionCreate,
    manager: HabitManager = Depends(get_habit_manager)
):
    """Record a completion for a habit.

    Returns the updated habit. If the habit has already been completed
    in the current period, returns HTTP 200 with a payload containing
    a ``message`` field plus the unchanged habit data so the client
    can render an idempotency notice.
    """
    habit = manager.get_habit(habit_id)
    
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")
    
    completion_date = completion_data.completed_at or datetime.now()
    success = manager.complete_habit(habit_id, completion_date)
    
    if not success:
        return JSONResponse(
            status_code=200,
            content={
                "message": "Habit already completed for this period",
                "habit": HabitResponse(
                    id=habit.id,
                    name=habit.name,
                    description=habit.description,
                    periodicity=habit.periodicity,
                    created_at=habit.created_at,
                    current_streak=habit.get_current_streak(),
                    longest_streak=habit.get_longest_streak(),
                    completion_count=len(habit.completions),
                    is_broken=habit.is_broken(),
                ).model_dump()
            }
        )
    
    # Reload habit to get updated data
    habit = manager.get_habit(habit_id)
    
    return HabitResponse(
        id=habit.id,
        name=habit.name,
        description=habit.description,
        periodicity=habit.periodicity,
        created_at=habit.created_at,
        current_streak=habit.get_current_streak(),
        longest_streak=habit.get_longest_streak(),
        completion_count=len(habit.completions),
        is_broken=habit.is_broken(),
    )


# Analytics endpoints

@router.get("/analytics/summary", response_model=AnalyticsResponse)
async def get_analytics_summary(
    manager: HabitManager = Depends(get_habit_manager)
):
    """Return aggregate metrics for the analytics dashboard."""
    habits = manager.get_all_habits()
    summary = analytics.get_analytics_summary(habits)
    
    return AnalyticsResponse(**summary)


@router.get("/analytics/longest-streak")
async def get_longest_streak(
    manager: HabitManager = Depends(get_habit_manager)
):
    """Return the single habit with the longest historical streak.

    Returns ``{"habit_name": null, "longest_streak": 0}`` when there
    are no habits or no completions.
    """
    habits = manager.get_all_habits()
    habit_name, streak = analytics.get_longest_streak_all(habits)
    
    return {
        "habit_name": habit_name,
        "longest_streak": streak
    }


@router.get("/analytics/struggling")
async def get_struggling_habits(
    days: int = Query(30, ge=1, le=365),
    manager: HabitManager = Depends(get_habit_manager)
):
    """List habits with a completion rate below 50% over ``days``.

    The ``days`` query parameter is clamped to ``[1, 365]`` by the
    schema validator.
    """
    habits = manager.get_all_habits()
    struggling = analytics.get_struggling_habits(habits, days)
    
    return {
        "period_days": days,
        "struggling_habits": struggling
    }


@router.get("/analytics/by-periodicity/{periodicity}")
async def get_habits_by_periodicity(
    periodicity: str,
    manager: HabitManager = Depends(get_habit_manager)
):
    """List habits filtered by ``periodicity``.

    Returns HTTP 400 when ``periodicity`` is not ``"daily"`` or
    ``"weekly"``. The body is intentionally lighter than
    :func:`get_habits` so the dashboard can render quick lists.
    """
    if periodicity not in ["daily", "weekly"]:
        raise HTTPException(
            status_code=400,
            detail="Periodicity must be 'daily' or 'weekly'"
        )
    
    habits = analytics.get_habits_by_periodicity(
        manager.get_all_habits(),
        periodicity
    )
    
    return {
        "periodicity": periodicity,
        "count": len(habits),
        "habits": [
            {
                "id": h.id,
                "name": h.name,
                "current_streak": h.get_current_streak(),
            }
            for h in habits
        ]
    }