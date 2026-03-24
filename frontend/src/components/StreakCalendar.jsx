import React from 'react'
import { getLastNDays } from '../utils/dateHelpers'

function StreakCalendar({ habit, days = 28 }) {
  const dates = getLastNDays(days)
  
  // Create a set of completion dates for quick lookup
  const completionSet = new Set()
  if (habit && habit.completions) {
    habit.completions.forEach(completion => {
      const date = new Date(completion)
      completionSet.add(date.toISOString().split('T')[0])
    })
  }

  // Group dates by week
  const weeks = []
  for (let i = 0; i < dates.length; i += 7) {
    weeks.push(dates.slice(i, i + 7))
  }

  const isCompleted = (date) => {
    const dateStr = date.toISOString().split('T')[0]
    return completionSet.has(dateStr)
  }

  const isToday = (date) => {
    const today = new Date()
    return (
      date.getDate() === today.getDate() &&
      date.getMonth() === today.getMonth() &&
      date.getFullYear() === today.getFullYear()
    )
  }

  const dayNames = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

  return (
    <div className="card">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">
        Activity Calendar
      </h3>
      
      <div className="overflow-x-auto">
        <div className="inline-block min-w-full">
          {/* Day names header */}
          <div className="flex mb-2">
            {dayNames.map(day => (
              <div
                key={day}
                className="w-10 h-6 flex items-center justify-center text-xs text-gray-500"
              >
                {day}
              </div>
            ))}
          </div>

          {/* Calendar grid */}
          <div className="space-y-1">
            {weeks.map((week, weekIndex) => (
              <div key={weekIndex} className="flex">
                {week.map((date, dayIndex) => {
                  const completed = isCompleted(date)
                  const today = isToday(date)
                  
                  return (
                    <div
                      key={dayIndex}
                      title={date.toLocaleDateString()}
                      className={`
                        w-10 h-10 flex items-center justify-center rounded-lg
                        text-sm font-medium transition-colors duration-200
                        ${
                          completed
                            ? 'bg-green-500 text-white'
                            : 'bg-gray-100 text-gray-400'
                        }
                        ${today ? 'ring-2 ring-primary-500 ring-offset-2' : ''}
                      `}
                    >
                      {date.getDate()}
                    </div>
                  )
                })}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Legend */}
      <div className="flex items-center space-x-4 mt-4 text-sm text-gray-600">
        <div className="flex items-center space-x-2">
          <div className="w-4 h-4 bg-green-500 rounded" />
          <span>Completed</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-4 h-4 bg-gray-100 rounded" />
          <span>Missed</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-4 h-4 bg-gray-100 rounded ring-2 ring-primary-500" />
          <span>Today</span>
        </div>
      </div>
    </div>
  )
}

export default StreakCalendar