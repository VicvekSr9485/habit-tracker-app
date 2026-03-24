import { useState, useEffect, useCallback } from 'react'
import * as api from '../services/apiService'

export function useHabits(periodicity = null) {
  const [habits, setHabits] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const fetchHabits = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await api.getHabits(periodicity)
      setHabits(data.habits)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [periodicity])

  useEffect(() => {
    fetchHabits()
  }, [fetchHabits])

  const createHabit = useCallback(async (habitData) => {
    try {
      const newHabit = await api.createHabit(habitData)
      setHabits(prev => [newHabit, ...prev])
      return newHabit
    } catch (err) {
      setError(err.message)
      throw err
    }
  }, [])

  const updateHabit = useCallback(async (habitId, habitData) => {
    try {
      const updatedHabit = await api.updateHabit(habitId, habitData)
      setHabits(prev =>
        prev.map(h => (h.id === habitId ? updatedHabit : h))
      )
      return updatedHabit
    } catch (err) {
      setError(err.message)
      throw err
    }
  }, [])

  const deleteHabit = useCallback(async (habitId) => {
    try {
      await api.deleteHabit(habitId)
      setHabits(prev => prev.filter(h => h.id !== habitId))
    } catch (err) {
      setError(err.message)
      throw err
    }
  }, [])

  const completeHabit = useCallback(async (habitId) => {
    try {
      const updatedHabit = await api.completeHabit(habitId)
      setHabits(prev =>
        prev.map(h => (h.id === habitId ? updatedHabit : h))
      )
      return updatedHabit
    } catch (err) {
      setError(err.message)
      throw err
    }
  }, [])

  return {
    habits,
    loading,
    error,
    refetch: fetchHabits,
    createHabit,
    updateHabit,
    deleteHabit,
    completeHabit,
  }
}

export default useHabits