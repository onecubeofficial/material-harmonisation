import React from 'react'

/**
 * SpecChips – renders extracted spec attributes as small coloured chips.
 * Props: specs (object), max (number, default 6)
 */
export default function SpecChips({ specs = {}, max = 6 }) {
  const entries = Object.entries(specs).slice(0, max)
  if (!entries.length) return <span className="text-gray-400 text-xs">–</span>

  return (
    <div className="flex flex-wrap gap-1">
      {entries.map(([k, v]) => (
        <span
          key={k}
          className="inline-flex items-center px-2 py-0.5 rounded text-xs bg-blue-50 text-blue-700 border border-blue-100"
          title={`${k}: ${v}`}
        >
          <span className="font-medium mr-1 opacity-60">{k.replace(/_/g, ' ')}</span>
          {String(v)}
        </span>
      ))}
      {Object.keys(specs).length > max && (
        <span className="text-xs text-gray-400">+{Object.keys(specs).length - max} more</span>
      )}
    </div>
  )
}
