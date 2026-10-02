import React, { useEffect, useState, useMemo } from 'react'
import { getMaster } from '../api'
import SpecChips from '../components/SpecChips'
import DataTable from '../components/DataTable'
import { Search, Download, ChevronDown, ChevronRight } from 'lucide-react'

export default function MasterDatabase() {
  const [data, setData] = useState({ items: [], total: 0 })
  const [loading, setLoading] = useState(false)
  const [expanded, setExpanded] = useState({})
  const [filters, setFilters] = useState({ search: '', category: '', page: 1, page_size: 15 })

  const load = async (f) => {
    setLoading(true)
    try {
      const params = Object.fromEntries(Object.entries(f).filter(([, v]) => v !== ''))
      const { data: res } = await getMaster(params)
      setData(res)
    } catch { /**/ } finally { setLoading(false) }
  }

  useEffect(() => { load(filters) }, [filters])

  const set = (k, v) => setFilters(p => ({ ...p, [k]: v, page: 1 }))

  const toggle = (id) => setExpanded(p => ({ ...p, [id]: !p[id] }))

  const columns = useMemo(() => [
    {
      header: 'Std Code',
      accessorKey: 'std_code',
      cell: ({ getValue }) => (
        <span className="font-mono font-bold text-primary-700">{getValue()}</span>
      ),
    },
    {
      header: 'Description',
      accessorKey: 'standard_description',
      cell: ({ getValue }) => (
        <span className="text-sm text-gray-900">{getValue()}</span>
      ),
    },
    {
      header: 'Category',
      accessorKey: 'category',
      cell: ({ getValue }) => (
        <span className="text-xs bg-indigo-50 text-indigo-700 px-2 py-0.5 rounded-full">{getValue() || '–'}</span>
      ),
    },
    {
      header: 'UoM',
      accessorKey: 'uom',
      cell: ({ getValue }) => <span className="text-xs text-gray-500">{getValue() || '–'}</span>,
    },
    {
      header: 'Specs',
      accessorKey: 'specs',
      cell: ({ getValue }) => <SpecChips specs={getValue() || {}} max={3} />,
    },
    {
      header: 'Mapped Codes',
      accessorKey: 'mapped_codes',
      cell: ({ getValue, row }) => {
        const codes = getValue() || []
        const isExp = expanded[row.original.id]
        return (
          <button
            onClick={e => { e.stopPropagation(); toggle(row.original.id) }}
            className="flex items-center gap-1 text-xs text-primary-600 hover:text-primary-700"
          >
            {codes.length} source code{codes.length !== 1 ? 's' : ''}
            {isExp ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
          </button>
        )
      },
    },
  ], [expanded])

  // Flatten rows: for each item, insert expanded sub-rows
  const flatRows = useMemo(() => {
    const rows = []
    for (const item of (data.items || [])) {
      rows.push({ ...item, _type: 'main' })
      if (expanded[item.id]) {
        rows.push({ ...item, _type: 'expanded' })
      }
    }
    return rows
  }, [data.items, expanded])

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Master Database</h1>
          <p className="text-gray-500 text-sm mt-0.5">Unified standard materials from approved clusters</p>
        </div>
        <a
          href={`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/master/export`}
          download
          className="btn-secondary"
        >
          <Download size={16} /> Export CSV
        </a>
      </div>

      {/* Filters */}
      <div className="card p-4 flex flex-wrap gap-3 items-end">
        <div className="relative">
          <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input className="input pl-9 w-60" placeholder="Search code, description…"
            value={filters.search} onChange={e => set('search', e.target.value)} />
        </div>
        <div>
          <label className="block text-xs text-gray-500 mb-1">Category</label>
          <input className="input w-44" placeholder="e.g. Fasteners"
            value={filters.category} onChange={e => set('category', e.target.value)} />
        </div>
        <span className="text-xs text-gray-400 self-end pb-2">{data.total} standard codes</span>
      </div>

      {/* Custom table with expandable rows */}
      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                {['Std Code', 'Description', 'Category', 'UoM', 'Specs', 'Mapped Codes'].map(h => (
                  <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide whitespace-nowrap">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {loading ? (
                <tr><td colSpan={6} className="px-4 py-10 text-center text-gray-400">Loading…</td></tr>
              ) : (data.items || []).length === 0 ? (
                <tr><td colSpan={6} className="px-4 py-10 text-center text-gray-400">No approved standard materials yet.</td></tr>
              ) : (
                (data.items || []).map(item => (
                  <React.Fragment key={item.id}>
                    <tr className="hover:bg-gray-50">
                      <td className="px-4 py-3 font-mono font-bold text-primary-700">{item.std_code}</td>
                      <td className="px-4 py-3 text-gray-900 max-w-xs">{item.standard_description}</td>
                      <td className="px-4 py-3">
                        <span className="text-xs bg-indigo-50 text-indigo-700 px-2 py-0.5 rounded-full">
                          {item.category || '–'}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-xs text-gray-500">{item.uom || '–'}</td>
                      <td className="px-4 py-3"><SpecChips specs={item.specs || {}} max={3} /></td>
                      <td className="px-4 py-3">
                        <button
                          onClick={() => toggle(item.id)}
                          className="flex items-center gap-1 text-xs text-primary-600 hover:text-primary-700"
                        >
                          {(item.mapped_codes || []).length} source code{(item.mapped_codes || []).length !== 1 ? 's' : ''}
                          {expanded[item.id] ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
                        </button>
                      </td>
                    </tr>
                    {expanded[item.id] && (
                      <tr className="bg-blue-50">
                        <td colSpan={6} className="px-8 py-3">
                          <table className="w-full text-xs border border-blue-100 rounded-lg overflow-hidden">
                            <thead className="bg-blue-100">
                              <tr>
                                <th className="px-3 py-2 text-left font-semibold text-blue-700">CPSE</th>
                                <th className="px-3 py-2 text-left font-semibold text-blue-700">Source Code</th>
                                <th className="px-3 py-2 text-left font-semibold text-blue-700">Source Description</th>
                              </tr>
                            </thead>
                            <tbody>
                              {(item.mapped_codes || []).map((mc, i) => (
                                <tr key={i} className="border-t border-blue-100">
                                  <td className="px-3 py-1.5 font-mono text-indigo-700">{mc.cpse_name}</td>
                                  <td className="px-3 py-1.5 font-mono">{mc.source_code}</td>
                                  <td className="px-3 py-1.5 text-gray-700">{mc.description}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Pagination */}
      {data.total > filters.page_size && (
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-500">
            {data.total} total standard codes
          </span>
          <div className="flex gap-2">
            <button disabled={filters.page <= 1} onClick={() => setFilters(p => ({ ...p, page: p.page - 1 }))}
              className="btn-secondary text-xs px-3 py-1.5 disabled:opacity-40">← Prev</button>
            <span className="text-sm text-gray-600 self-center">Page {filters.page} of {data.total_pages}</span>
            <button disabled={filters.page >= data.total_pages} onClick={() => setFilters(p => ({ ...p, page: p.page + 1 }))}
              className="btn-secondary text-xs px-3 py-1.5 disabled:opacity-40">Next →</button>
          </div>
        </div>
      )}
    </div>
  )
}
