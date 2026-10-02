import React, { useEffect, useState } from 'react'
import { getAudit } from '../api'
import { ScrollText, RefreshCw } from 'lucide-react'

const ACTION_COLORS = {
  upload:  'bg-blue-100 text-blue-700',
  process: 'bg-purple-100 text-purple-700',
  approve: 'bg-green-100 text-green-700',
  reject:  'bg-red-100 text-red-700',
  edit:    'bg-amber-100 text-amber-700',
}

const fmt = (ts) => {
  if (!ts) return '–'
  return new Date(ts).toLocaleString('en-IN', {
    day: '2-digit', month: 'short', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

export default function AuditLog() {
  const [data, setData] = useState({ items: [], total: 0, page: 1, total_pages: 1 })
  const [loading, setLoading] = useState(false)
  const [page, setPage] = useState(1)

  const load = async (p = 1) => {
    setLoading(true)
    try {
      const { data: res } = await getAudit({ page: p, page_size: 50 })
      setData(res)
    } catch { /**/ } finally { setLoading(false) }
  }

  useEffect(() => { load(page) }, [page])

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Audit Log</h1>
          <p className="text-gray-500 text-sm mt-0.5">All system actions with timestamps</p>
        </div>
        <button onClick={() => load(page)} className="btn-secondary">
          <RefreshCw size={15} /> Refresh
        </button>
      </div>

      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                {['#', 'Time', 'Action', 'Entity', 'Entity ID', 'Details'].map(h => (
                  <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {loading ? (
                <tr><td colSpan={6} className="px-4 py-10 text-center text-gray-400">Loading…</td></tr>
              ) : data.items.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-4 py-12 text-center">
                    <ScrollText size={32} className="text-gray-300 mx-auto mb-2" />
                    <p className="text-gray-400">No audit entries yet.</p>
                  </td>
                </tr>
              ) : (
                data.items.map(log => (
                  <tr key={log.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-xs text-gray-400 font-mono">{log.id}</td>
                    <td className="px-4 py-3 text-xs text-gray-500 whitespace-nowrap">{fmt(log.created_at)}</td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${ACTION_COLORS[log.action] || 'bg-gray-100 text-gray-600'}`}>
                        {log.action}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-700">{log.entity || '–'}</td>
                    <td className="px-4 py-3 text-sm text-gray-700 font-mono">{log.entity_id ?? '–'}</td>
                    <td className="px-4 py-3 text-xs text-gray-500 max-w-xs">
                      <pre className="whitespace-pre-wrap font-mono text-xs leading-relaxed">
                        {log.details && Object.keys(log.details).length > 0
                          ? JSON.stringify(log.details, null, 2)
                          : '–'}
                      </pre>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Pagination */}
      {data.total_pages > 1 && (
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-500">{data.total} total entries</span>
          <div className="flex gap-2">
            <button disabled={page <= 1} onClick={() => setPage(p => p - 1)}
              className="btn-secondary text-xs px-3 py-1.5 disabled:opacity-40">← Prev</button>
            <span className="text-sm self-center text-gray-600">Page {page} of {data.total_pages}</span>
            <button disabled={page >= data.total_pages} onClick={() => setPage(p => p + 1)}
              className="btn-secondary text-xs px-3 py-1.5 disabled:opacity-40">Next →</button>
          </div>
        </div>
      )}
    </div>
  )
}
