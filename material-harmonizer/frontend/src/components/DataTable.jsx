import React from 'react'
import {
  useReactTable,
  getCoreRowModel,
  flexRender,
} from '@tanstack/react-table'
import { ChevronLeft, ChevronRight } from 'lucide-react'

/**
 * DataTable – a generic table built on TanStack Table v8.
 *
 * Props:
 *   columns    – TanStack column definitions
 *   data       – row array
 *   total      – total count (for server-side pagination)
 *   page       – current page (1-based)
 *   pageSize   – rows per page
 *   onPage     – (newPage) => void
 *   loading    – boolean
 *   onRowClick – (row) => void  (optional)
 */
export default function DataTable({
  columns, data, total = 0, page = 1, pageSize = 20,
  onPage, loading = false, onRowClick,
}) {
  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
    manualPagination: true,
    pageCount: Math.ceil(total / pageSize),
  })

  const totalPages = Math.max(1, Math.ceil(total / pageSize))

  return (
    <div>
      <div className="overflow-x-auto rounded-xl border border-gray-200">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-200">
            {table.getHeaderGroups().map(hg => (
              <tr key={hg.id}>
                {hg.headers.map(header => (
                  <th
                    key={header.id}
                    className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide whitespace-nowrap"
                  >
                    {flexRender(header.column.columnDef.header, header.getContext())}
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody className="divide-y divide-gray-100 bg-white">
            {loading ? (
              <tr>
                <td colSpan={columns.length} className="px-4 py-10 text-center text-gray-400">
                  Loading…
                </td>
              </tr>
            ) : table.getRowModel().rows.length === 0 ? (
              <tr>
                <td colSpan={columns.length} className="px-4 py-10 text-center text-gray-400">
                  No records found.
                </td>
              </tr>
            ) : (
              table.getRowModel().rows.map(row => (
                <tr
                  key={row.id}
                  onClick={() => onRowClick && onRowClick(row.original)}
                  className={`transition-colors ${onRowClick ? 'cursor-pointer hover:bg-blue-50' : 'hover:bg-gray-50'}`}
                >
                  {row.getVisibleCells().map(cell => (
                    <td key={cell.id} className="px-4 py-3 text-gray-700 align-top">
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {total > pageSize && (
        <div className="flex items-center justify-between mt-4">
          <span className="text-sm text-gray-500">
            Showing {Math.min((page - 1) * pageSize + 1, total)}–{Math.min(page * pageSize, total)} of {total}
          </span>
          <div className="flex items-center gap-1">
            <button
              onClick={() => onPage(page - 1)}
              disabled={page <= 1}
              className="p-1.5 rounded-lg border border-gray-300 disabled:opacity-40 hover:bg-gray-100 transition-colors"
            >
              <ChevronLeft size={16} />
            </button>
            {Array.from({ length: Math.min(7, totalPages) }, (_, i) => {
              let p = i + 1
              if (totalPages > 7) {
                const mid = Math.min(Math.max(page, 4), totalPages - 3)
                p = mid - 3 + i
              }
              return (
                <button
                  key={p}
                  onClick={() => onPage(p)}
                  className={`min-w-[32px] h-8 rounded-lg text-sm transition-colors
                    ${p === page
                      ? 'bg-primary-600 text-white font-semibold'
                      : 'border border-gray-300 hover:bg-gray-100 text-gray-700'}`}
                >
                  {p}
                </button>
              )
            })}
            <button
              onClick={() => onPage(page + 1)}
              disabled={page >= totalPages}
              className="p-1.5 rounded-lg border border-gray-300 disabled:opacity-40 hover:bg-gray-100 transition-colors"
            >
              <ChevronRight size={16} />
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
