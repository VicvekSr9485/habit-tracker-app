"""FastAPI application entry point.

Run directly with ``python main.py`` to start a Uvicorn server, or via
``uvicorn main:app --reload`` for hot-reload during development. The
``lifespan`` handler bootstraps a demo database on first launch so the
frontend has data to render against.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from api.routes import router
from fixtures.sample_data import load_sample_data
from api.dependencies import get_storage


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage app-wide startup and shutdown.

    On startup, seed the database with sample habits if it is empty.
    On shutdown, close the singleton SQLite connection so the file
    handle is released cleanly.
    """
    storage = get_storage()
    habits = storage.load_all_habits()

    if len(habits) == 0:
        print("Loading sample data...")
        load_sample_data(storage)
        print("Sample data loaded successfully!")

    yield

    storage.close()


app = FastAPI(
    title="Habit Tracker API",
    description="A comprehensive habit tracking application",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router)


@app.get("/")
async def root():
    """Return a small index payload pointing at the OpenAPI docs."""
    return {
        "message": "Welcome to Habit Tracker API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health")
async def health_check():
    """Liveness probe — always returns ``{"status": "healthy"}``."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)