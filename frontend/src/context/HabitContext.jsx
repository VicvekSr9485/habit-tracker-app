import React, { createContext, useContext, useState, useCallback } from 'react'
import * as api from '../services/apiService'

const HabitContext = createContext(null)

export function HabitProvider({ children }) {
  const [habits, setHabits] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const fetchHabits = useCallback(async (periodicity = null) => {
    setLoading(true)
    setError(null)
    try {
      const data = await api.getHabits(periodicity)
      setHabits(data.habits)
      return data.habits
    } catch (err) {
      setError(err.message)
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  const createHabit = useCallback(async (habitData) => {
    setLoading(true)
    setError(null)
    try {
      const newHabit = await api.createHabit(habitData)
      setHabits(prev => [newHabit, ...prev])
      return newHabit
    } catch (err) {
      setError(err.message)
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  const updateHabit = useCallback(async (habitId, habitData) => {
    setLoading(true)
    setError(null)
    try {
      const updatedHabit = await api.updateHabit(habitId, habitData)
      setHabits(prev =>
        prev.map(h => (h.id === habitId ? updatedHabit : h))
      )
      return updatedHabit
    } catch (err) {
      setError(err.message)
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  const deleteHabit = useCallback(async (habitId) => {
    setLoading(true)
    setError(null)
    try {
      await api.deleteHabit(habitId)
      setHabits(prev => prev.filter(h => h.id !== habitId))
    } catch (err) {
      setError(err.message)
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  const completeHabit = useCallback(async (habitId) => {
    setError(null)
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

  const value = {
    habits,
    loading,
    error,
    fetchHabits,
    createHabit,
    updateHabit,
    deleteHabit,
    completeHabit,
  }

  return (
    <HabitContext.Provider value={value}>
      {children}
    </HabitContext.Provider>
  )
}

export function useHabitContext() {
  const context = useContext(HabitContext)
  if (!context) {
    throw new Error('useHabitContext must be used within a HabitProvider')
  }
  return context
}

export default HabitContext