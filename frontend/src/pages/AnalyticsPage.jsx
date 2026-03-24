import React, { useEffect, useState } from 'react'
import { TrendingUp, Award, AlertTriangle, PieChart } from 'lucide-react'
import AnalyticsChart from '../components/AnalyticsChart'
import { useAnalytics } from '../hooks/useAnalytics'
import { useHabitContext } from '../context/HabitContext'

function AnalyticsPage() {
  const { summary, longestStreak, strugglingHabits, loading, error } = useAnalytics()
  const { habits, fetchHabits } = useHabitContext()

  useEffect(() => {
    fetchHabits()
  }, [fetchHabits])

  // Prepare chart data
  const streakChartData = habits.map(habit => ({
    name: habit.name.length > 15 ? habit.name.substring(0, 15) + '...' : habit.name,
    value: habit.current_streak,
  }))

  const periodicityChartData = [
    { name: 'Daily', value: summary?.daily_habits || 0 },
    { name: 'Weekly', value: summary?.weekly_habits || 0 },
  ].filter(d => d.value > 0)

  const completionChartData = habits.map(habit => ({
    name: habit.name.length > 15 ? habit.name.substring(0, 15) + '...' : habit.name,
    value: habit.completion_count,
  }))

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Analytics</h1>
        <p className="text-gray-600 mt-1">
          Insights into your habit tracking progress
        </p>
      </div>

      {/* Error Message */}
      {error && (
        <div className="p-4 bg-red-100 border border-red-200 rounded-lg">
          <p className="text-red-700">{error}</p>
        </div>
      )}

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Total Habits */}
        <div className="card">
          <div className="flex items-center space-x-4">
            <div className="p-3 bg-blue-100 rounded-lg">
              <PieChart className="h-6 w-6 text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Total Habits</p>
              <p className="text-2xl font-bold text-gray-900">
                {summary?.total_habits || 0}
              </p>
            </div>
          </div>
        </div>

        {/* Average Streak */}
        <div className="card">
          <div className="flex items-center space-x-4">
            <div className="p-3 bg-green-100 rounded-lg">
              <TrendingUp className="h-6 w-6 text-green-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Average Streak</p>
              <p className="text-2xl font-bold text-gray-900">
                {summary?.average_streak?.toFixed(1) || 0}
              </p>
            </div>
          </div>
        </div>

        {/* Longest Streak */}
        <div className="card">
          <div className="flex items-center space-x-4">
            <div className="p-3 bg-yellow-100 rounded-lg">
              <Award className="h-6 w-6 text-yellow-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Longest Streak</p>
              <p className="text-2xl font-bold text-gray-900">
                {longestStreak?.longest_streak || 0}
              </p>
              {longestStreak?.habit_name && (
                <p className="text-xs text-gray-500 truncate max-w-[150px]">
                  {longestStreak.habit_name}
                </p>
              )}
            </div>
          </div>
        </div>

        {/* Total Completions */}
        <div className="card">
          <div className="flex items-center space-x-4">
            <div className="p-3 bg-purple-100 rounded-lg">
              <span className="text-xl">✅</span>
            </div>
            <div>
              <p className="text-sm text-gray-600">Total Completions</p>
              <p className="text-2xl font-bold text-gray-900">
                {summary?.total_completions || 0}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Current Streaks Chart */}
        <AnalyticsChart
          type="bar"
          data={streakChartData}
          title="Current Streaks by Habit"
        />

        {/* Habit Distribution Chart */}
        <AnalyticsChart
          type="pie"
          data={periodicityChartData}
          title="Habits by Periodicity"
        />

        {/* Completions Chart */}
        <AnalyticsChart
          type="bar"
          data={completionChartData}
          title="Total Completions by Habit"
        />

        {/* Struggling Habits */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center space-x-2">
            <AlertTriangle className="h-5 w-5 text-yellow-500" />
            <span>Habits Needing Attention</span>
          </h3>
          
          {strugglingHabits.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <div className="text-4xl mb-2">🎉</div>
              <p>Great job! All habits are on track.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {strugglingHabits.map((habit, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-3 bg-yellow-50 rounded-lg"
                >
                  <div>
                    <p className="font-medium text-gray-900">{habit.name}</p>
                    <p className="text-sm text-gray-500">
                      {habit.actual}/{habit.expected} completions
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-lg font-bold text-yellow-600">
                      {habit.completion_rate}%
                    </p>
                    <p className="text-xs text-gray-500">completion rate</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Habit Details Table */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          All Habits Overview
        </h3>
        
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead>
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Habit
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Periodicity
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Current Streak
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Longest Streak
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Completions
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {habits.map((habit) => (
                <tr key={habit.id} className="hover:bg-gray-50">
                  <td className="px-4 py-4 whitespace-nowrap">
                    <p className="text-sm font-medium text-gray-900">
                      {habit.name}
                    </p>
                  </td>
                  <td className="px-4 py-4 whitespace-nowrap">
                    <span
                      className={`
                        px-2 py-1 text-xs font-medium rounded-full
                        ${
                          habit.periodicity === 'daily'
                            ? 'bg-blue-100 text-blue-700'
                            : 'bg-purple-100 text-purple-700'
                        }
                      `}
                    >
                      {habit.periodicity}
                    </span>
                  </td>
                  <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-900">
                    {habit.current_streak} 🔥
                  </td>
                  <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-900">
                    {habit.longest_streak}
                  </td>
                  <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-900">
                    {habit.completion_count}
                  </td>
                  <td className="px-4 py-4 whitespace-nowrap">
                    <span
                      className={`
                        px-2 py-1 text-xs font-medium rounded-full
                        ${
                          habit.is_broken
                            ? 'bg-red-100 text-red-700'
                            : 'bg-green-100 text-green-700'
                        }
                      `}
                    >
                      {habit.is_broken ? 'Broken' : 'Active'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

export default AnalyticsPage