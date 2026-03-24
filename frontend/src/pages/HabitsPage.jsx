import React, { useEffect, useMemo, useState } from 'react'
import HabitCard from '../components/HabitCard'
import HabitForm from '../components/HabitForm'
import PeriodFilter from '../components/PeriodFilter'
import { useHabitContext } from '../context/HabitContext'

function HabitsPage() {
  const {
    habits,
    loading,
    error,
    fetchHabits,
    createHabit,
    updateHabit,
    deleteHabit,
    completeHabit,
  } = useHabitContext()

  const [showCreateForm, setShowCreateForm] = useState(false)
  const [editingHabit, setEditingHabit] = useState(null)
  const [periodicityFilter, setPeriodicityFilter] = useState('')

  useEffect(() => {
    fetchHabits(periodicityFilter || null)
  }, [fetchHabits, periodicityFilter])

  const visibleHabits = useMemo(() => {
    if (!periodicityFilter) return habits
    return habits.filter((habit) => habit.periodicity === periodicityFilter)
  }, [habits, periodicityFilter])

  const handleCreate = async (formData) => {
    await createHabit(formData)
    setShowCreateForm(false)
  }

  const handleUpdate = async (formData) => {
    if (!editingHabit) return
    await updateHabit(editingHabit.id, formData)
    setEditingHabit(null)
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Habits</h1>
          <p className="text-gray-600 mt-1">Create, edit, and track your habits.</p>
        </div>

        <button
          className="btn btn-primary"
          onClick={() => {
            setEditingHabit(null)
            setShowCreateForm((prev) => !prev)
          }}
        >
          {showCreateForm ? 'Close Form' : 'New Habit'}
        </button>
      </div>

      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <PeriodFilter value={periodicityFilter} onChange={setPeriodicityFilter} />
        <p className="text-sm text-gray-600">
          Showing {visibleHabits.length} {visibleHabits.length === 1 ? 'habit' : 'habits'}
        </p>
      </div>

      {error && (
        <div className="p-3 rounded-lg border border-red-200 bg-red-100 text-red-700">
          {error}
        </div>
      )}

      {showCreateForm && (
        <HabitForm
          onSubmit={handleCreate}
          onCancel={() => setShowCreateForm(false)}
        />
      )}

      {editingHabit && (
        <HabitForm
          habit={editingHabit}
          onSubmit={handleUpdate}
          onCancel={() => setEditingHabit(null)}
        />
      )}

      {loading && habits.length === 0 ? (
        <div className="flex items-center justify-center h-48">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary-600"></div>
        </div>
      ) : visibleHabits.length === 0 ? (
        <div className="card text-center py-10">
          <h2 className="text-xl font-semibold text-gray-900">No habits found</h2>
          <p className="text-gray-600 mt-2">Create one to start building streaks.</p>
        </div>
      ) : (
        <div className="grid gap-4">
          {visibleHabits.map((habit) => (
            <HabitCard
              key={habit.id}
              habit={habit}
              onComplete={completeHabit}
              onDelete={deleteHabit}
              onEdit={setEditingHabit}
            />
          ))}
        </div>
      )}
    </div>
  )
}

export default HabitsPage
