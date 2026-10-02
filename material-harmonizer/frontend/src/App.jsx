import React from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Upload from './pages/Upload'
import Matching from './pages/Matching'
import ClusterDetail from './pages/ClusterDetail'
import MasterDatabase from './pages/MasterDatabase'
import AuditLog from './pages/AuditLog'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard"   element={<Dashboard />} />
          <Route path="upload"      element={<Upload />} />
          <Route path="matching"    element={<Matching />} />
          <Route path="matching/:id" element={<ClusterDetail />} />
          <Route path="master"      element={<MasterDatabase />} />
          <Route path="audit"       element={<AuditLog />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
