import React, { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getCluster, approveCluster, rejectCluster } from '../api'
import ScoreBadge from '../components/ScoreBadge'
import SpecChips from '../components/SpecChips'
import {
  ArrowLeft, CheckCircle2, XCircle, Trash2,
  ChevronDown, ChevronUp, Info, Loader2,
} from 'lucide-react'
import toast from 'react-hot-toast'

export default function ClusterDetail() {
  const { id } = useParams()
  const navigate = useNavigate()

  const [cluster, setCluster] = useState(null)
  const [loading, setLoading] = useState(true)
  const [removing, setRemoving] = useState(new Set())
  const [stdDesc, setStdDesc] = useState('')
  const [actioning, setActioning] = useState(false)
  const [expanded, setExpanded] = useState({})

  const fetch = async () => {
    setLoading(true)
    try {
      const { data } = await getCluster(id)
      setCluster(data)
      setStdDesc(data.suggested_description || '')
    } catch {
      toast.error('Failed to load cluster')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetch() }, [id])

  const toggleRemove = (memberId) => {
    setRemoving(prev => {
      const s = new Set(prev)
      s.has(memberId) ? s.delete(memberId) : s.add(memberId)
      return s
    })
  }

  const handleApprove = async () => {
    setActioning(true)
    try {
      const { data } = await approveCluster(id, {
        standard_description: stdDesc,
        remove_member_ids: Array.from(removing),
      })
      toast.success(data.message)
      navigate('/matching')
    } catch (e) {
      toast.error('Approve failed: ' + (e.response?.data?.detail || e.message))
    } finally {
      setActioning(false)
    }
  }

  const handleReject = async () => {
    if (!window.confirm('Reject this cluster?')) return
    setActioning(true)
    try {
      await rejectCluster(id)
      toast('Cluster rejected', { icon: '🚫' })
      navigate('/matching')
    } catch (e) {
      toast.error('Reject failed: ' + (e.response?.data?.detail || e.message))
    } finally {
      setActioning(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 size={32} className="animate-spin text-primary-600" />
      </div>
    )
  }
  if (!cluster) return <p className="text-gray-500">Cluster not found.</p>

  const activeMembers = cluster.members.filter(m => !removing.has(m.id))

  return (
    <div className="max-w-5xl space-y-5">
      {/* Header */}
      <div className="flex items-center gap-3">
        <button onClick={() => navigate('/matching')} className="btn-secondary p-2">
          <ArrowLeft size={18} />
        </button>
        <div>
          <h1 className="text-xl font-bold text-gray-900">
            Cluster #{cluster.id}
            <span className="ml-3 font-mono text-primary-600">{cluster.suggested_std_code || '–'}</span>
          </h1>
          <p className="text-gray-500 text-sm">
            {cluster.category} · {cluster.member_count} members · {cluster.cpse_count} CPSEs
          </p>
        </div>
        <div className="ml-auto">
          <ScoreBadge score={cluster.confidence} />
        </div>
      </div>

      {/* Suggested description editor */}
      <div className="card p-5">
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Suggested Standard Description
          <span className="text-gray-400 font-normal ml-1">(editable)</span>
        </label>
        <input
          className="input"
          value={stdDesc}
          onChange={e => setStdDesc(e.target.value)}
          disabled={cluster.status !== 'pending'}
        />
        <p className="text-xs text-gray-400 mt-1">
          Code: <span className="font-mono font-semibold">{cluster.suggested_std_code || '–'}</span>
          {' · '} Category: {cluster.category} · Sub: {cluster.subcategory}
        </p>
      </div>

      {/* Members */}
      <div className="card overflow-hidden">
        <div className="px-5 py-3 border-b border-gray-200 flex items-center justify-between bg-gray-50">
          <h2 className="text-sm font-semibold text-gray-700">
            Members ({activeMembers.length} active
            {removing.size > 0 && <span className="text-red-500">, {removing.size} to remove</span>}
            )
          </h2>
          <span className="text-xs text-gray-400">Click row to expand explanation</span>
        </div>

        <div className="divide-y divide-gray-100">
          {cluster.members.map(member => {
            const isRemoved = removing.has(member.id)
            const isExpanded = expanded[member.id]
            const exp = member.explanation

            return (
              <div key={member.id} className={`transition-colors ${isRemoved ? 'opacity-40 bg-red-50' : ''}`}>
                <div
                  className="px-5 py-4 flex items-start gap-4 cursor-pointer hover:bg-gray-50"
                  onClick={() => setExpanded(prev => ({ ...prev, [member.id]: !prev[member.id] }))}
                >
                  {/* CPSE badge */}
                  <span className="text-xs bg-indigo-100 text-indigo-700 px-2 py-1 rounded font-mono whitespace-nowrap">
                    {member.cpse_name}
                  </span>

                  {/* Main info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start gap-2">
                      <span className="font-mono text-xs text-gray-500 whitespace-nowrap">{member.source_code}</span>
                      <p className="text-sm text-gray-900 font-medium line-clamp-2">{member.description}</p>
                    </div>
                    <div className="mt-1.5">
                      <SpecChips specs={member.specs} max={5} />
                    </div>
                    {member.uom && (
                      <span className="text-xs text-gray-400 mt-1 inline-block">UoM: {member.uom}</span>
                    )}
                  </div>

                  {/* Similarity bar */}
                  <div className="w-28 flex-shrink-0 text-right">
                    <p className="text-xs text-gray-500 mb-1">Similarity</p>
                    <div className="w-full bg-gray-200 rounded-full h-1.5">
                      <div
                        className="bg-primary-500 h-1.5 rounded-full"
                        style={{ width: `${Math.round(member.centroid_similarity * 100)}%` }}
                      />
                    </div>
                    <p className="text-xs text-gray-600 mt-0.5">{(member.centroid_similarity * 100).toFixed(1)}%</p>
                  </div>

                  {/* Remove toggle */}
                  {cluster.status === 'pending' && (
                    <button
                      onClick={e => { e.stopPropagation(); toggleRemove(member.id) }}
                      className={`flex-shrink-0 p-1.5 rounded-lg transition-colors
                        ${isRemoved
                          ? 'bg-red-100 text-red-600 hover:bg-red-200'
                          : 'bg-gray-100 text-gray-400 hover:bg-red-100 hover:text-red-500'}`}
                      title={isRemoved ? 'Restore to cluster' : 'Remove from cluster'}
                    >
                      <Trash2 size={14} />
                    </button>
                  )}

                  {isExpanded ? <ChevronUp size={16} className="text-gray-400 flex-shrink-0 mt-1" />
                               : <ChevronDown size={16} className="text-gray-400 flex-shrink-0 mt-1" />}
                </div>

                {/* Expanded explanation */}
                {isExpanded && exp && (
                  <div className="px-5 pb-4 bg-blue-50 border-t border-blue-100">
                    <div className="flex items-start gap-2 mt-3">
                      <Info size={14} className="text-blue-500 mt-0.5 flex-shrink-0" />
                      <div className="text-sm text-blue-800 space-y-1">
                        <p className="font-medium">{exp.reason}</p>
                        <div className="flex gap-4 text-xs mt-1">
                          <span>Embedding sim: <b>{(exp.embedding_sim * 100).toFixed(1)}%</b></span>
                          <span>Fuzzy sim: <b>{(exp.fuzzy_sim * 100).toFixed(1)}%</b></span>
                        </div>
                        {exp.matching_specs.length > 0 && (
                          <p className="text-xs">
                            ✅ Matching specs: {exp.matching_specs.join(', ')}
                          </p>
                        )}
                        {exp.differing_specs.length > 0 && (
                          <p className="text-xs text-amber-700">
                            ⚠️ Differing specs: {exp.differing_specs.join(', ')}
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </div>

      {/* Actions */}
      {cluster.status === 'pending' && (
        <div className="flex items-center gap-3">
          <button onClick={handleApprove} disabled={actioning} className="btn-primary">
            {actioning ? <Loader2 size={16} className="animate-spin" /> : <CheckCircle2 size={16} />}
            Approve Cluster
          </button>
          <button onClick={handleReject} disabled={actioning} className="btn-danger">
            <XCircle size={16} />
            Reject Cluster
          </button>
          {removing.size > 0 && (
            <span className="text-sm text-gray-500">
              {removing.size} member(s) will be excluded from the standard code
            </span>
          )}
        </div>
      )}
      {cluster.status !== 'pending' && (
        <div className={`card p-4 ${cluster.status === 'approved' ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}`}>
          <p className={`text-sm font-medium ${cluster.status === 'approved' ? 'text-green-800' : 'text-red-800'}`}>
            This cluster has been <b>{cluster.status}</b>.
          </p>
        </div>
      )}
    </div>
  )
}
