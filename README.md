# Habit Tracker Application

A comprehensive, full-stack habit tracking application built with FastAPI and React.

## Technical Documentation

- Backend: [backend/TECHNICAL_DOCUMENTATION](backend/TECHNICAL_DOCUMENTATION.md)
- Frontend: [frontend/TECHNICAL_DOCUMENTATION](frontend/TECHNICAL_DOCUMENTATION.md)

## 🚀 Features

*   **Habit Management:** Create, read, update, and delete habits.
*   **Streak Tracking:** Calculate and visualize current and longest streaks.
*   **Analytics Dashboard:** View habit completion rates and trends over time using charts.
*   **Calendar View:** Visualize habit consistency on a calendar interface.
*   **Responsive UI:** Clean and modern interface built with Tailwind CSS.

## 🛠️ Tech Stack

### Backend
*   **Framework:** FastAPI (Python 3)
*   **Database:** SQLite (built-in)
*   **Validation:** Pydantic
*   **Testing:** Pytest

### Frontend
*   **Framework:** React 18
*   **Build Tool:** Vite
*   **Styling:** Tailwind CSS, PostCSS
*   **Routing:** React Router DOM
*   **Icons:** Lucide React
*   **Charts:** Recharts
*   **HTTP Client:** Axios

## 📂 Project Structure

```text
habit-tracker-app/
├── backend/            # FastAPI backend application
│   ├── analytics/      # Habit data analysis and statistics
│   ├── api/            # REST API routes and dependencies
│   ├── cli/            # Command-line interface tools
│   ├── core/           # Business logic and habit management
│   ├── fixtures/       # Sample data generation
│   ├── models/         # Pydantic validation and domain models
│   ├── storage/        # Database interface and SQLite implementation
│   ├── tests/          # Pytest test suites
│   ├── main.py         # Application entry point
│   └── requirements.txt# Python dependencies
├── frontend/           # React frontend application
│   ├── src/
│   │   ├── components/ # Reusable UI components (Cards, Forms, Charts)
│   │   ├── context/    # React context for state management
│   │   ├── hooks/      # Custom React hooks (useHabits, useAnalytics)
│   │   ├── pages/      # Main application views
│   │   ├── services/   # API client configuration
│   │   └── utils/      # Helper functions (Dates, Streaks)
│   ├── package.json    # Node.js dependencies
│   └── vite.config.js  # Vite configuration
└── docker-compose.yml  # Docker container configuration
```

## 🏃‍♂️ Getting Started

### Prerequisites

Make sure you have the following installed:
*   [Docker](https://www.docker.com/) and Docker Compose (Recommended)
*   **OR**
*   [Python 3.10+](https://www.python.org/)
*   [Node.js 18+](https://nodejs.org/) and npm

### Method 1: Using Docker (Recommended)

The easiest way to run the application is using Docker Compose.

1.  Clone the repository and navigate to the project root.
2.  Start the containers:
    ```bash
    docker-compose up --build
    ```
3.  Access the application:
    *   **Frontend:** `http://localhost:3000`
    *   **Backend API:** `http://localhost:8000`
    *   **Interactive API Docs (Swagger UI):** `http://localhost:8000/docs`

*Note: The backend automatically loads sample data on the first start if the database is empty.*

### Method 2: Manual Setup

If you prefer to run the application locally without Docker:

#### 1. Setup Backend

Navigate to the backend directory:
```bash
cd backend
```

Create and activate a virtual environment:
```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
```

Install dependencies:
```bash
pip install -r requirements.txt
```

Run the backend server:
```bash
python main.py
# The API will be available at http://localhost:8000
```

#### 2. Setup Frontend

Open a new terminal and navigate to the frontend directory:
```bash
cd frontend
```

Create a `.env` file with the backend API URL:
```bash
echo "VITE_API_URL=http://localhost:8000" > .env
```

Install dependencies:
```bash
npm install
```

Start the Vite development server:
```bash
npm run dev
# The frontend will be available at http://localhost:5173
```

## 🧪 Testing

### Backend Tests

Run tests inside Docker (recommended when running via compose):

```bash
docker compose exec -T backend pytest -q
```

Run tests locally from the backend folder:

```bash
cd backend
pytest -q
```

To run with coverage:
```bash
pytest --cov=.
```

### CLI Functionality Testing

Test CLI commands inside Docker:

```bash
docker compose exec -T backend python -m cli.controller --help
docker compose exec -T backend python -m cli.controller create --name "CLI Exercise Habit" --description "Habit created for CLI testing" --periodicity daily
docker compose exec -T backend python -m cli.controller list
docker compose exec -T backend python -m cli.controller complete 1
docker compose exec -T backend python -m cli.controller info 1
docker compose exec -T backend python -m cli.controller analyze
docker compose exec -T backend python -m cli.controller longest
printf 'y\n' | docker compose exec -T backend python -m cli.controller delete 1
docker compose exec -T backend python -m cli.controller list
```

Run CLI locally from the backend folder:

```bash
cd backend
python -m cli.controller --help
```

## 📝 License

This project is open-source and available under the MIT License.
