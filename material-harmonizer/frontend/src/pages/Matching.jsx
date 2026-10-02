import React, { useEffect, useState, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { getClusters } from '../api'
import DataTable from '../components/DataTable'
import ScoreBadge from '../components/ScoreBadge'
import { Search, Filter, ChevronRight } from 'lucide-react'

const STATUS_OPTS = ['', 'pending', 'approved', 'rejected']

export default function Matching() {
  const navigate = useNavigate()
  const [data, setData] = useState({ items: [], total: 0, page: 1 })
  const [loading, setLoading] = useState(false)

  const [filters, setFilters] = useState({
    status: '',
    category: '',
    min_confidence: '',
    search: '',
    page: 1,
    page_size: 20,
  })

  const load = async (f) => {
    setLoading(true)
    try {
      const params = Object.fromEntries(
        Object.entries(f).filter(([, v]) => v !== '' && v != null)
      )
      const { data: res } = await getClusters(params)
      setData(res)
    } catch { /* ignore */ }
    finally { setLoading(false) }
  }

  useEffect(() => { load(filters) }, [filters])

  const set = (k, v) => setFilters(prev => ({ ...prev, [k]: v, page: 1 }))

  const columns = useMemo(() => [
    {
      header: 'ID',
      accessorKey: 'id',
      cell: ({ getValue }) => <span className="font-mono text-xs text-gray-500">#{getValue()}</span>,
    },
    {
      header: 'Category',
      accessorKey: 'category',
      cell: ({ getValue }) => (
        <span className="text-xs bg-indigo-50 text-indigo-700 px-2 py-0.5 rounded-full">
          {getValue() || '–'}
        </span>
      ),
    },
    {
      header: 'Suggested Code',
      accessorKey: 'suggested_std_code',
      cell: ({ getValue }) => (
        <span className="font-mono text-sm font-semibold text-primary-700">
          {getValue() || '–'}
        </span>
      ),
    },
    {
      header: 'Description',
      accessorKey: 'suggested_description',
      cell: ({ getValue }) => (
        <span className="text-sm text-gray-700 line-clamp-2 max-w-xs">{getValue() || '–'}</span>
      ),
    },
    {
      header: 'Members',
      accessorKey: 'member_count',
      cell: ({ getValue, row }) => (
        <span className="text-sm text-gray-700">
          {getValue()} <span className="text-gray-400 text-xs">({row.original.cpse_count} CPSEs)</span>
        </span>
      ),
    },
    {
      header: 'Confidence',
      accessorKey: 'confidence',
      cell: ({ getValue }) => <ScoreBadge score={getValue()} />,
    },
    {
      header: 'Status',
      accessorKey: 'status',
      cell: ({ getValue }) => {
        const v = getValue()
        const cls = v === 'approved' ? 'badge-approved' : v === 'rejected' ? 'badge-rejected' : 'badge-pending'
        return <span className={cls}>{v}</span>
      },
    },
    {
      header: '',
      id: 'action',
      cell: () => <ChevronRight size={16} className="text-gray-400" />,
    },
  ], [])

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">AI Matching Clusters</h1>
        <p className="text-gray-500 text-sm mt-0.5">Review detected duplicate material groups</p>
      </div>

      {/* Filters */}
      <div className="card p-4 flex flex-wrap gap-3 items-end">
        <div className="relative">
          <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            className="input pl-9 w-56"
            placeholder="Search description, code…"
            value={filters.search}
            onChange={e => set('search', e.target.value)}
          />
        </div>

        <div>
          <label className="block text-xs text-gray-500 mb-1">Status</label>
          <select className="input w-36" value={filters.status} onChange={e => set('status', e.target.value)}>
            {STATUS_OPTS.map(s => (
              <option key={s} value={s}>{s || 'All statuses'}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs text-gray-500 mb-1">Category</label>
          <input
            className="input w-44"
            placeholder="e.g. Fasteners"
            value={filters.category}
            onChange={e => set('category', e.target.value)}
          />
        </div>

        <div>
          <label className="block text-xs text-gray-500 mb-1">Min Confidence</label>
          <input
            type="number" min={0} max={1} step={0.01}
            className="input w-32"
            placeholder="0.80"
            value={filters.min_confidence}
            onChange={e => set('min_confidence', e.target.value)}
          />
        </div>

        <span className="text-xs text-gray-400 self-end pb-2">
          {data.total} cluster{data.total !== 1 ? 's' : ''} found
        </span>
      </div>

      <DataTable
        columns={columns}
        data={data.items || []}
        total={data.total}
        page={filters.page}
        pageSize={filters.page_size}
        onPage={p => setFilters(prev => ({ ...prev, page: p }))}
        loading={loading}
        onRowClick={row => navigate(`/matching/${row.id}`)}
      />
    </div>
  )
}
