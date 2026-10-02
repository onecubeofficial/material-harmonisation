import React, { useEffect, useRef, useState } from 'react'
import { getStats, startProcess, getStatus } from '../api'
import StatCard from '../components/StatCard'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend,
} from 'recharts'
import {
  Package, Building2, GitMerge, TrendingUp,
  IndianRupee, Play, CheckCircle2, AlertCircle, Loader2,
} from 'lucide-react'
import toast from 'react-hot-toast'

const PIE_COLORS = ['#f59e0b', '#22c55e', '#ef4444']

const fmt = (n) =>
  n == null ? '–' : new Intl.NumberFormat('en-IN').format(Math.round(n))

const fmtCurrency = (n) =>
  n == null ? '–' : '₹ ' + new Intl.NumberFormat('en-IN', {
    maximumFractionDigits: 0,
  }).format(n)

export default function Dashboard() {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [pipelineStatus, setPipelineStatus] = useState({ state: 'idle', progress_percent: 0, message: '' })
  const pollRef = useRef(null)

  const fetchStats = async () => {
    try {
      const { data } = await getStats()
      setStats(data)
    } catch {
      // silently ignore on dashboard load
    } finally {
      setLoading(false)
    }
  }

  const pollStatus = async () => {
    try {
      const { data } = await getStatus()
      setPipelineStatus(data)
      if (data.state === 'done') {
        clearInterval(pollRef.current)
        toast.success('Processing complete!')
        fetchStats()
      } else if (data.state === 'error') {
        clearInterval(pollRef.current)
        toast.error('Pipeline error: ' + data.message)
      }
    } catch {/* ignore */}
  }

  useEffect(() => {
    fetchStats()
    pollStatus()
    return () => clearInterval(pollRef.current)
  }, [])

  const handleRun = async () => {
    try {
      await startProcess()
      setPipelineStatus({ state: 'running', progress_percent: 0, message: 'Starting…', step: '' })
      clearInterval(pollRef.current)
      pollRef.current = setInterval(pollStatus, 1500)
      toast('Pipeline started', { icon: '🚀' })
    } catch (e) {
      toast.error('Failed to start: ' + (e.response?.data?.detail || e.message))
    }
  }

  const isRunning = pipelineStatus.state === 'running'

  const pieData = stats ? [
    { name: 'Pending',  value: stats.clusters_by_status.pending },
    { name: 'Approved', value: stats.clusters_by_status.approved },
    { name: 'Rejected', value: stats.clusters_by_status.rejected },
  ] : []

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-500 text-sm mt-0.5">Material harmonization overview</p>
        </div>
        <button onClick={handleRun} disabled={isRunning} className="btn-primary">
          {isRunning
            ? <><Loader2 size={16} className="animate-spin" /> Running…</>
            : <><Play size={16} /> Run Processing</>}
        </button>
      </div>

      {/* Pipeline progress bar */}
      {(isRunning || pipelineStatus.state === 'done') && (
        <div className="card p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700 flex items-center gap-2">
              {isRunning && <Loader2 size={14} className="animate-spin text-primary-600" />}
              {pipelineStatus.state === 'done' && <CheckCircle2 size={14} className="text-green-500" />}
              {pipelineStatus.state === 'error' && <AlertCircle size={14} className="text-red-500" />}
              {pipelineStatus.step || pipelineStatus.message || 'Pipeline'}
            </span>
            <span className="text-sm text-gray-500">{pipelineStatus.progress_percent}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-primary-600 h-2 rounded-full transition-all duration-500"
              style={{ width: `${pipelineStatus.progress_percent}%` }}
            />
          </div>
          {pipelineStatus.message && (
            <p className="text-xs text-gray-500 mt-1">{pipelineStatus.message}</p>
          )}
        </div>
      )}

      {/* Stat cards */}
      {loading ? (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="card p-5 h-24 animate-pulse bg-gray-100" />
          ))}
        </div>
      ) : stats && (
        <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
          <StatCard title="Total Materials" value={fmt(stats.total_materials)}
            icon={<Package size={20} />} color="bg-primary-600" />
          <StatCard title="CPSEs" value={fmt(stats.total_cpses)}
            icon={<Building2 size={20} />} color="bg-indigo-600" />
          <StatCard title="Duplicate Clusters" value={fmt(stats.duplicate_clusters_found)}
            subtitle={`${stats.duplicate_percentage}% of materials`}
            icon={<GitMerge size={20} />} color="bg-amber-500" />
          <StatCard title="Approved Clusters" value={fmt(stats.clusters_by_status.approved)}
            subtitle={`${fmt(stats.code_reduction_raw)} → ${fmt(stats.code_reduction_standard)} codes`}
            icon={<CheckCircle2 size={20} />} color="bg-green-600" />
          <StatCard
            title="Est. Savings (8%)"
            value={fmtCurrency(stats.estimated_savings)}
            subtitle="Estimate based on approved clusters"
            icon={<IndianRupee size={20} />}
            color="bg-teal-600"
          />
        </div>
      )}

      {/* Charts row */}
      {stats && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Duplicates by category */}
          <div className="card p-5 lg:col-span-2">
            <h2 className="text-base font-semibold text-gray-900 mb-4">Duplicate Clusters by Category</h2>
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={stats.top_categories_by_duplicates} margin={{ top: 4, right: 8, bottom: 40, left: 0 }}>
                <XAxis
                  dataKey="category"
                  tick={{ fontSize: 11 }}
                  angle={-35}
                  textAnchor="end"
                  interval={0}
                />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip />
                <Bar dataKey="count" fill="#2563eb" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Cluster status pie */}
          <div className="card p-5">
            <h2 className="text-base font-semibold text-gray-900 mb-4">Cluster Status</h2>
            <ResponsiveContainer width="100%" height={260}>
              <PieChart>
                <Pie data={pieData} cx="50%" cy="45%" innerRadius={60} outerRadius={95}
                  dataKey="value" paddingAngle={3} label={({ name, value }) => `${name}: ${value}`}
                  labelLine={false}
                >
                  {pieData.map((_, i) => (
                    <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                  ))}
                </Pie>
                <Legend />
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Materials per CPSE */}
      {stats && stats.materials_per_cpse.length > 0 && (
        <div className="card p-5">
          <h2 className="text-base font-semibold text-gray-900 mb-4">Materials per CPSE</h2>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={stats.materials_per_cpse} margin={{ top: 4, right: 8, bottom: 20, left: 0 }}>
              <XAxis dataKey="cpse_name" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Bar dataKey="count" fill="#6366f1" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  )
}
