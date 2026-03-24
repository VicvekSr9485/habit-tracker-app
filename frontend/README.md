# Frontend Technical Documentation

This directory contains the React frontend for the Habit Tracker Application, scaffolded via Vite.

## Architecture

The application is a Single Page Application (SPA) built with React. It uses functional components and custom hooks for scalable state management and business logic.

### Directory Structure

*   **`src/main.jsx` & `src/App.jsx`**: React application entry point and main router setup.
*   **`src/pages/`**: Main layout views corresponding to different routes:
    *   `DashboardPage.jsx`: The homepage summarizing habits and streaks.
    *   `HabitsPage.jsx`: Page to manage (create/edit/delete) individual habits.
    *   `AnalyticsPage.jsx`: Dedicated view for deep-dive statistics and charts.
*   **`src/components/`**: Reusable presentational or minor stateful UI pieces (e.g., `HabitCard.jsx`, `StreakCalendar.jsx`, `AnalyticsChart.jsx`).
*   **`src/hooks/`**: Custom React context hooks to encapsulate data fetching and local state (e.g., `useHabits.js`, `useAnalytics.js`).
*   **`src/context/`**: React Context providers (e.g., `HabitContext.jsx`) used to share state globally across the application.
*   **`src/services/`**: API integration layer (`apiService.js`), utilizing Axios to communicate with the backend FastAPI endpoints.
*   **`src/utils/`**: Shared helper functions for repetitive tasks like date parsing (`dateHelpers.js`) and streak calculation algorithms (`streakCalculator.js`).

## Technologies Used

*   **React 18**: Frontend UI library utilizing functional components and hooks.
*   **Vite**: Extremely fast frontend build tool and development server.
*   **Tailwind CSS**: Utility-first CSS framework for rapid UI styling.
*   **React Router DOM**: Client-side routing.
*   **Axios**: Promise-based HTTP client for API requests.
*   **Recharts**: Composable charting library built on React components.
*   **Lucide React**: Open-source icon set.

## Routing

The app utilizes `react-router-dom` for client-side navigation. Key routes generally include:
*   `/` - Dashboard view.
*   `/habits` - Complete list of habits.
*   `/analytics` - Detailed charts and tracking.

## API Communication

All communication with the backend is abstracted into `services/apiService.js`. Components rely on hooks (like `useHabits`) to trigger these service methods rather than calling Axios directly. This keeps the UI components decoupled from the immediate HTTP layer.
  
Configure the API base URL via the `.env` file containing `VITE_API_URL`. When using docker-compose, this is typically `http://localhost:8000`.

## Local Setup & Development

1.  **Dependencies**: Install the Node modules.
    ```bash
    npm install
    ```
2.  **Environment Variables**: Create a `.env` file (if not present) and configure `VITE_API_URL` if different from the default.
3.  **Start Development Server**:
    ```bash
    npm run dev
    ```
4.  **Building for Production**:
    ```bash
    npm run build
    ```
    This compiles a production-ready bundle into the `dist/` directory.

## Linting

This project uses ESLint configured for React and Vite. To run the linter:
```bash