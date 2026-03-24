import React from 'react'

function PeriodFilter({ value, onChange }) {
  const options = [
    { value: '', label: 'All Habits' },
    { value: 'daily', label: 'Daily' },
    { value: 'weekly', label: 'Weekly' },
  ]

  return (
    <div className="flex items-center space-x-2">
      <span className="text-sm text-gray-600">Filter:</span>
      <div className="flex rounded-lg overflow-hidden border border-gray-200">
        {options.map((option) => (
          <button
            key={option.value}
            onClick={() => onChange(option.value)}
            className={`
              px-4 py-2 text-sm font-medium transition-colors duration-200
              ${
                value === option.value
                  ? 'bg-primary-600 text-white'
                  : 'bg-white text-gray-600 hover:bg-gray-50'
              }
            `}
          >
            {option.label}
          </button>
        ))}
      </div>
    </div>
  )
}

export default PeriodFilter