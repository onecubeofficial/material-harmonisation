import React from 'react'
import { Outlet, NavLink } from 'react-router-dom'
import {
  LayoutDashboard, Upload, GitMerge, Database,
  ScrollText, Cpu, ChevronRight,
} from 'lucide-react'

const NAV_ITEMS = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/upload',    icon: Upload,          label: 'Upload Data' },
  { to: '/matching',  icon: GitMerge,        label: 'AI Matching' },
  { to: '/master',    icon: Database,        label: 'Master Database' },
  { to: '/audit',     icon: ScrollText,      label: 'Audit Log' },
]

export default function Layout() {
  return (
    <div className="flex h-screen overflow-hidden bg-gray-50">
      {/* ── Sidebar ──────────────────────────────────────────────────── */}
      <aside className="w-64 flex-shrink-0 bg-primary-900 text-white flex flex-col">
        {/* Logo */}
        <div className="px-6 py-5 border-b border-primary-800">
          <div className="flex items-center gap-3">
            <div className="p-1.5 bg-primary-600 rounded-lg">
              <Cpu size={20} className="text-white" />
            </div>
            <div>
              <p className="font-bold text-sm leading-tight">Material Harmonizer</p>
              <p className="text-primary-300 text-xs">AI-Driven Standardization</p>
            </div>
          </div>
        </div>

        {/* Nav links */}
        <nav className="flex-1 py-4 px-3 space-y-1 overflow-y-auto">
          {NAV_ITEMS.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors
                 ${isActive
                   ? 'bg-primary-600 text-white'
                   : 'text-primary-200 hover:bg-primary-800 hover:text-white'}`
              }
            >
              <Icon size={18} />
              <span className="flex-1">{label}</span>
            </NavLink>
          ))}
        </nav>

        {/* Footer */}
        <div className="px-4 py-3 border-t border-primary-800">
          <p className="text-primary-400 text-xs text-center">
            CPSE Material Harmonization v1.0
          </p>
        </div>
      </aside>

      {/* ── Main area ─────────────────────────────────────────────────── */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top header */}
        <header className="bg-white border-b border-gray-200 px-6 py-3 flex items-center gap-2">
          <span className="text-gray-400 text-sm">Ministry of Heavy Industries</span>
          <ChevronRight size={14} className="text-gray-300" />
          <span className="text-gray-700 text-sm font-medium">
            AI-Driven Material Code Standardization
          </span>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
