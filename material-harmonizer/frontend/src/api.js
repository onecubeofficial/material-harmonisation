/**
 * api.js – Axios instance configured for the backend.
 * Base URL defaults to http://localhost:8000 but can be overridden
 * via the VITE_API_URL environment variable.
 */
import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  headers: { 'Content-Type': 'application/json' },
})

// ── Upload ─────────────────────────────────────────────────────────────────────
export const uploadFile = (cpseName, file) => {
  const form = new FormData()
  form.append('cpse_name', cpseName)
  form.append('file', file)
  return api.post('/api/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

// ── Process ────────────────────────────────────────────────────────────────────
export const startProcess  = ()  => api.post('/api/process')
export const getStatus     = ()  => api.get('/api/process/status')

// ── Clusters ───────────────────────────────────────────────────────────────────
export const getClusters = (params) => api.get('/api/clusters', { params })
export const getCluster  = (id)     => api.get(`/api/clusters/${id}`)
export const approveCluster = (id, body) => api.post(`/api/clusters/${id}/approve`, body)
export const rejectCluster  = (id)       => api.post(`/api/clusters/${id}/reject`)

// ── Master ─────────────────────────────────────────────────────────────────────
export const getMaster = (params) => api.get('/api/master', { params })

// ── Stats ──────────────────────────────────────────────────────────────────────
export const getStats = () => api.get('/api/stats')

// ── ERP ────────────────────────────────────────────────────────────────────────
export const erpLookup = (cpse, code) =>
  api.get('/api/erp/lookup', { params: { cpse, code } })

// ── Audit ──────────────────────────────────────────────────────────────────────
export const getAudit = (params) => api.get('/api/audit', { params })

// ── Health ─────────────────────────────────────────────────────────────────────
export const health = () => api.get('/api/health')

export default api
