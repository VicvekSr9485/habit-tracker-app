import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Plus, TrendingUp, Calendar, Target, AlertTriangle } from 'lucide-react'
import HabitCard from '../components/HabitCard'
import { useHabitContext } from '../context/HabitContext'
import { useAnalytics } from '../hooks/useAnalytics'

function DashboardPage() {
  const { habits, loading, error, fetchHabits, completeHabit, deleteHabit } = useHabitContext()
  const { summary, longestStreak, loading: analyticsLoading } = useAnalytics()
  const [editingHabit, setEditingHabit] = useState(null)

  useEffect(() => {
    fetchHabits()
  }, [fetchHabits])

  const handleComplete = async (habitId) => {
    await completeHabit(habitId)
  }

  const handleDelete = async (habitId) => {
    await deleteHabit(habitId)
  }

  const handleEdit = (habit) => {
    setEditingHabit(habit)
  }

  // Get today's date formatted
  const today = new Date().toLocaleDateString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })

  // Calculate habits due today
  const habitsDueToday = habits.filter(h => !h.is_broken)

  if (loading && habits.length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-600 mt-1">{today}</p>
        </div>
        <Link to="/habits" className="btn btn-primary flex items-center space-x-2">
          <Plus className="h-5 w-5" />
          <span>New Habit</span>
        </Link>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Total Habits */}
        <div className="card">
          <div className="flex items-center space-x-4">
            <div className="p-3 bg-blue-100 rounded-lg">
              <Target className="h-6 w-6 text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Total Habits</p>
              <p className="text-2xl font-bold text-gray-900">
                {summary?.total_habits || 0}
              </p>
            </div>
          </div>
        </div>

        {/* Active Streaks */}
        <div className="card">
          <div className="flex items-center space-x-4">
            <div className="p-3 bg-green-100 rounded-lg">
              <TrendingUp className="h-6 w-6 text-green-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Active Habits</p>
              <p className="text-2xl font-bold text-gray-900">
                {habitsDueToday.length}
              </p>
            </div>
          </div>
        </div>

        {/* Total Completions */}
        <div className="card">
          <div className="flex items-center space-x-4">
            <div className="p-3 bg-purple-100 rounded-lg">
              <Calendar className="h-6 w-6 text-purple-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Total Completions</p>
              <p className="text-2xl font-bold text-gray-900">
                {summary?.total_completions || 0}
              </p>
            </div>
          </div>
        </div>

        {/* Longest Streak */}
        <div className="card">
          <div className="flex items-center space-x-4">
            <div className="p-3 bg-orange-100 rounded-lg">
              <span className="text-2xl">🔥</span>
            </div>
            <div>
              <p className="text-sm text-gray-600">Longest Streak</p>
              <p className="text-2xl font-bold text-gray-900">
                {longestStreak?.longest_streak || 0} days
              </p>
              {longestStreak?.habit_name && (
                <p className="text-xs text-gray-500">{longestStreak.habit_name}</p>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="p-4 bg-red-100 border border-red-200 rounded-lg flex items-center space-x-2">
          <AlertTriangle className="h-5 w-5 text-red-600" />
          <p className="text-red-700">{error}</p>
        </div>
      )}

      {/* Habits List */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900">Your Habits</h2>
          <Link to="/habits" className="text-primary-600 hover:text-primary-700 text-sm font-medium">
            View All →
          </Link>
        </div>

        {habits.length === 0 ? (
          <div className="card text-center py-12">
            <div className="text-6xl mb-4">🎯</div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              No habits yet
            </h3>
            <p className="text-gray-600 mb-4">
              Start building positive habits today!
            </p>
            <Link to="/habits" className="btn btn-primary inline-flex items-center space-x-2">
              <Plus className="h-5 w-5" />
              <span>Create Your First Habit</span>
            </Link>
          </div>
        ) : (
          <div className="grid gap-4">
            {habits.slice(0, 5).map((habit) => (
              <HabitCard
                key={habit.id}
                habit={habit}
                onComplete={handleComplete}
                onDelete={handleDelete}
                onEdit={handleEdit}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default DashboardPage