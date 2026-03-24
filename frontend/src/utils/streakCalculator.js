/**
 * Calculate streak statistics for visualization
 * @param {Object} habit - Habit object with completions
 * @returns {Object} Streak statistics
 */
export function calculateStreakStats(habit) {
  return {
    current: habit.current_streak || 0,
    longest: habit.longest_streak || 0,
    completionCount: habit.completion_count || 0,
    isBroken: habit.is_broken || false,
  }
}

/**
 * Get streak status and color
 * @param {number} streak - Current streak value
 * @param {string} periodicity - Habit periodicity
 * @returns {Object} Status object with label and color
 */
export function getStreakStatus(streak, periodicity) {
  const unit = periodicity === 'daily' ? 'day' : 'week'
  const units = periodicity === 'daily' ? 'days' : 'weeks'

  if (streak === 0) {
    return {
      label: 'No streak',
      color: 'gray',
      emoji: '😴',
    }
  } else if (streak < 3) {
    return {
      label: `${streak} ${streak === 1 ? unit : units}`,
      color: 'yellow',
      emoji: '🌱',
    }
  } else if (streak < 7) {
    return {
      label: `${streak} ${units}`,
      color: 'green',
      emoji: '🌿',
    }
  } else if (streak < 14) {
    return {
      label: `${streak} ${units}`,
      color: 'blue',
      emoji: '🌳',
    }
  } else if (streak < 30) {
    return {
      label: `${streak} ${units}`,
      color: 'purple',
      emoji: '🔥',
    }
  } else {
    return {
      label: `${streak} ${units}`,
      color: 'orange',
      emoji: '⭐',
    }
  }
}

/**
 * Calculate completion percentage for a period
 * @param {number} completions - Number of completions
 * @param {number} expected - Expected number of completions
 * @returns {number} Percentage (0-100)
 */
export function calculateCompletionRate(completions, expected) {
  if (expected === 0) return 0
  return Math.min(100, Math.round((completions / expected) * 100))
}

/**
 * Get color class based on completion rate
 * @param {number} rate - Completion rate (0-100)
 * @returns {string} Tailwind color class
 */
export function getCompletionRateColor(rate) {
  if (rate >= 80) return 'text-green-600'
  if (rate >= 60) return 'text-yellow-600'
  if (rate >= 40) return 'text-orange-600'
  return 'text-red-600'
}