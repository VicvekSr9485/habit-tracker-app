import { useState, useEffect, useCallback } from 'react'
import * as api from '../services/apiService'

export function useAnalytics() {
  const [summary, setSummary] = useState(null)
  const [longestStreak, setLongestStreak] = useState(null)
  const [strugglingHabits, setStrugglingHabits] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const fetchAnalytics = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [summaryData, streakData, strugglingData] = await Promise.all([
        api.getAnalyticsSummary(),
        api.getLongestStreak(),
        api.getStrugglingHabits(30),
      ])
      
      setSummary(summaryData)
      setLongestStreak(streakData)
      setStrugglingHabits(strugglingData.struggling_habits || [])
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchAnalytics()
  }, [fetchAnalytics])

  return {
    summary,
    longestStreak,
    strugglingHabits,
    loading,
    error,
    refetch: fetchAnalytics,
  }
}

export default useAnalytics