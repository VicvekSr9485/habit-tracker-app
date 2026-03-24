# Frontend Technical Documentation

## 1. Overview

The frontend is a React + Vite single-page application for managing habits and visualizing habit analytics.

Primary responsibilities:
- Render dashboard, habit management, and analytics views.
- Handle form validation and local UI states.
- Integrate with backend REST API through a centralized Axios service.
- Present chart-based and tabular insights.

## 2. Runtime Architecture

Application boot sequence:
1. main.jsx mounts React root, BrowserRouter, and HabitProvider.
2. App.jsx provides top-level layout and route mapping.
3. Route pages consume shared state from HabitContext and analytics hooks.
4. API operations flow through services/apiService.js.
5. Tailwind utility classes and component classes style all views.

State model:
- Global shared habit state is maintained in HabitContext.
- useAnalytics is separate and page-local, with its own loading/error lifecycle.

## 3. Routing and Page Layer

Defined routes in App.jsx:
- / -> DashboardPage
- /habits -> HabitsPage
- /analytics -> AnalyticsPage

Observed implementation note:
- HabitsPage.jsx currently contains DashboardPage implementation content (duplicate/misaligned file content).
- This can cause route behavior mismatch and should be corrected.

### 3.1 DashboardPage
Responsibilities:
- Loads habits from context on mount.
- Loads analytics summary and longest streak via useAnalytics.
- Displays stat cards, quick actions, and recent habit list.
- Triggers complete and delete operations through context actions.

### 3.2 HabitsPage
Current state:
- File content is duplicated from dashboard logic and exports DashboardPage.
- Expected dedicated habit management page implementation appears missing.

### 3.3 AnalyticsPage
Responsibilities:
- Fetches analytics summary/longest streak/struggling habits via hook.
- Builds chart datasets from current habits.
- Renders bar and pie charts.
- Shows habit-level table with status badges and streak metrics.

## 4. Component Layer

### 4.1 HabitForm
- Supports create/edit mode via optional habit prop.
- Validates:
  - name required, <= 100 chars
  - description required, <= 500 chars
- Handles local submit error and loading states.

### 4.2 AnalyticsChart
- Wrapper over Recharts components.
- Supports type="bar" and type="pie" rendering modes.
- Handles empty data states.

### 4.3 PeriodFilter
- Small segmented control to filter by periodicity.
- Options:
  - all
  - daily
  - weekly

### 4.4 StreakCalendar
- Displays completion activity heatmap-style grid for last N days.
- Uses dateHelpers.getLastNDays().
- Marks today and completion states with visual indicators.

### 4.5 Navigation and HabitCard (Observed mismatch)
- Files frontend/src/components/Navigation.jsx and frontend/src/components/HabitCard.jsx currently contain streak utility helper functions instead of React components.
- This is a structural/implementation defect and can break imports and runtime behavior.

## 5. State Management and Data Access

### 5.1 HabitContext
Exposes:
- habits
- loading
- error
- fetchHabits
- createHabit
- updateHabit
- deleteHabit
- completeHabit

Behavior:
- Centralizes CRUD operations and updates in-memory list optimistically after API success.
- Throws errors back to consumers while also storing error state.

### 5.2 Custom Hooks
- useHabits(periodicity): local state wrapper around API methods.
- useAnalytics(): fetches summary, longest streak, and struggling habits in parallel.

Note:
- Both HabitContext and useHabits manage similar habit-fetching concerns, which can introduce duplicated state pathways.

## 6. API Integration

services/apiService.js:
- Axios instance uses VITE_API_URL with fallback http://localhost:8000.
- Request interceptor currently pass-through (reserved for future auth).
- Response interceptor unwraps response.data and normalizes error message.

Habit API methods:
- getHabits
- getHabit
- createHabit
- updateHabit
- deleteHabit
- completeHabit

Analytics API methods:
- getAnalyticsSummary
- getLongestStreak
- getStrugglingHabits
- getHabitsByPeriodicity

## 7. Styling System

Tailwind setup:
- Config in tailwind.config.js with custom primary color palette.
- index.css defines utility component classes:
  - .btn variants
  - .card
  - .input
  - .label

Design observations:
- App uses consistent utility-first class patterns.
- Shared class abstractions reduce duplication for controls/cards.

## 8. Build and Tooling

Dependencies and scripts from package.json:
- npm run dev
- npm run build
- npm run lint
- npm run preview

Dev tooling:
- Vite + @vitejs/plugin-react.
- ESLint with react, react-hooks, and react-refresh rules.
- PostCSS with Tailwind and Autoprefixer.

Vite server:
- Port: 3000
- Proxy: /api -> http://localhost:8000

## 9. Environment and Deployment

Local environment variable:
- VITE_API_URL=http://localhost:8000

Container runtime:
- frontend Dockerfile based on node:18-alpine.
- docker-compose runs npm run dev -- --host and maps port 3000.

## 10. Testing Status

No frontend unit/integration tests are currently present in this codebase.

Recommendation:
- Add testing stack (Vitest + React Testing Library) for:
  - Component render behavior
  - Hook data-loading and error handling
  - Route-level smoke tests
