import React from 'react'

/**
 * ScoreBadge – colour-coded confidence badge.
 * >= 0.92 → green (high confidence)
 * 0.80–0.92 → amber (needs review)
 * < 0.80 → red (low)
 */
export default function ScoreBadge({ score }) {
  if (score == null) return <span className="text-gray-400 text-xs">–</span>

  const pct = Math.round(score * 100)

  let cls = 'bg-red-100 text-red-700'
  let label = 'Low'
  if (score >= 0.92) { cls = 'bg-green-100 text-green-700'; label = 'High' }
  else if (score >= 0.80) { cls = 'bg-amber-100 text-amber-700'; label = 'Review' }

  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold ${cls}`}>
      {pct}% <span className="font-normal opacity-70">{label}</span>
    </span>
  )
}
