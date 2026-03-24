import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    // Add any auth headers here if needed
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
apiClient.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const message = error.response?.data?.detail || error.message || 'An error occurred'
    return Promise.reject(new Error(message))
  }
)

// Habit API calls
export const getHabits = async (periodicity = null) => {
  const params = periodicity ? { periodicity } : {}
  return apiClient.get('/api/habits', { params })
}

export const getHabit = async (habitId) => {
  return apiClient.get(`/api/habits/${habitId}`)
}

export const createHabit = async (habitData) => {
  return apiClient.post('/api/habits', habitData)
}

export const updateHabit = async (habitId, habitData) => {
  return apiClient.put(`/api/habits/${habitId}`, habitData)
}

export const deleteHabit = async (habitId) => {
  return apiClient.delete(`/api/habits/${habitId}`)
}

export const completeHabit = async (habitId, completedAt = null) => {
  const response = await apiClient.post(`/api/habits/${habitId}/complete`, {
    completed_at: completedAt,
  })

  return response?.habit || response
}

// Analytics API calls
export const getAnalyticsSummary = async () => {
  return apiClient.get('/api/analytics/summary')
}

export const getLongestStreak = async () => {
  return apiClient.get('/api/analytics/longest-streak')
}

export const getStrugglingHabits = async (days = 30) => {
  return apiClient.get('/api/analytics/struggling', { params: { days } })
}

export const getHabitsByPeriodicity = async (periodicity) => {
  return apiClient.get(`/api/analytics/by-periodicity/${periodicity}`)
}

export default apiClient