import React from 'react'
import { NavLink } from 'react-router-dom'

function Navigation() {
  const navItems = [
    { path: '/', label: 'Dashboard' },
    { path: '/habits', label: 'Habits' },
    { path: '/analytics', label: 'Analytics' },
  ]

  return (
    <header className="bg-white border-b border-gray-200 sticky top-0 z-20">
      <div className="container mx-auto max-w-7xl px-4">
        <div className="h-16 flex items-center justify-between">
          <h1 className="text-lg sm:text-xl font-semibold text-gray-900">
            Habit Tracker
          </h1>

          <nav className="flex items-center gap-2 sm:gap-3">
            {navItems.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                end={item.path === '/'}
                className={({ isActive }) =>
                  [
                    'px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                    isActive
                      ? 'bg-primary-600 text-white'
                      : 'text-gray-700 hover:bg-gray-100',
                  ].join(' ')
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
        </div>
      </div>
    </header>
  )
}

export default Navigation
