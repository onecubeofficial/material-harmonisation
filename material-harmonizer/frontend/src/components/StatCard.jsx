import React from 'react'

/**
 * StatCard – a simple dashboard metric tile.
 * Props: title, value, subtitle, icon (React element), color (tailwind bg class)
 */
export default function StatCard({ title, value, subtitle, icon, color = 'bg-primary-600' }) {
  return (
    <div className="card p-5 flex items-start gap-4">
      <div className={`${color} p-3 rounded-xl flex-shrink-0`}>
        <span className="text-white">{icon}</span>
      </div>
      <div className="min-w-0">
        <p className="text-xs font-medium text-gray-500 uppercase tracking-wide truncate">{title}</p>
        <p className="mt-0.5 text-2xl font-bold text-gray-900 truncate">{value}</p>
        {subtitle && (
          <p className="mt-0.5 text-xs text-gray-500 truncate">{subtitle}</p>
        )}
      </div>
    </div>
  )
}
