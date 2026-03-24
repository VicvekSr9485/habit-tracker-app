import React from 'react'

function HabitCard({ habit, onComplete, onDelete, onEdit }) {
  const statusClass = habit.is_broken
    ? 'bg-red-100 text-red-700'
    : 'bg-green-100 text-green-700'

  const handleDelete = () => {
    if (onDelete && window.confirm(`Delete habit "${habit.name}"?`)) {
      onDelete(habit.id)
    }
  }

  return (
    <article className="card">
      <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div className="space-y-2">
          <div className="flex items-center gap-2 flex-wrap">
            <h3 className="text-lg font-semibold text-gray-900">{habit.name}</h3>
            <span className="px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-700">
              {habit.periodicity}
            </span>
            <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusClass}`}>
              {habit.is_broken ? 'Broken' : 'Active'}
            </span>
          </div>

          <p className="text-gray-600">{habit.description}</p>

          <div className="grid grid-cols-3 gap-4 text-sm">
            <div>
              <p className="text-gray-500">Current streak</p>
              <p className="font-semibold text-gray-900">{habit.current_streak}</p>
            </div>
            <div>
              <p className="text-gray-500">Longest streak</p>
              <p className="font-semibold text-gray-900">{habit.longest_streak}</p>
            </div>
            <div>
              <p className="text-gray-500">Completions</p>
              <p className="font-semibold text-gray-900">{habit.completion_count}</p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2 self-end md:self-start">
          {onEdit && (
            <button className="btn btn-secondary" onClick={() => onEdit(habit)}>
              Edit
            </button>
          )}
          {onComplete && (
            <button className="btn btn-success" onClick={() => onComplete(habit.id)}>
              Complete
            </button>
          )}
          {onDelete && (
            <button className="btn btn-danger" onClick={handleDelete}>
              Delete
            </button>
          )}
        </div>
      </div>
    </article>
  )
}

export default HabitCard
