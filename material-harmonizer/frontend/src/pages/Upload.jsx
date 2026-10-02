import React, { useCallback, useRef, useState } from 'react'
import { uploadFile } from '../api'
import { Upload as UploadIcon, FileSpreadsheet, X, CheckCircle2, AlertCircle } from 'lucide-react'
import toast from 'react-hot-toast'
import * as XLSX from 'xlsx'

export default function Upload() {
  const [cpseName, setCpseName] = useState('')
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState([])
  const [previewHeaders, setPreviewHeaders] = useState([])
  const [uploading, setUploading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const fileInputRef = useRef()

  const parsePreview = (f) => {
    const reader = new FileReader()
    reader.onload = (e) => {
      try {
        const wb = XLSX.read(e.target.result, { type: 'array' })
        const ws = wb.Sheets[wb.SheetNames[0]]
        const rows = XLSX.utils.sheet_to_json(ws, { header: 1 })
        if (rows.length === 0) return
        const headers = rows[0].map(String)
        const dataRows = rows.slice(1, 11)
        setPreviewHeaders(headers)
        setPreview(dataRows.map(r => headers.map((_, i) => r[i] ?? '')))
      } catch {
        setPreviewHeaders([])
        setPreview([])
      }
    }
    reader.readAsArrayBuffer(f)
  }

  const handleFile = (f) => {
    if (!f) return
    const ext = f.name.split('.').pop().toLowerCase()
    if (!['xlsx', 'xls', 'csv'].includes(ext)) {
      toast.error('Only .xlsx, .xls or .csv files are accepted')
      return
    }
    setFile(f)
    setResult(null)
    setError(null)
    parsePreview(f)
  }

  const onDrop = useCallback((e) => {
    e.preventDefault()
    handleFile(e.dataTransfer.files[0])
  }, [])

  const handleSubmit = async () => {
    if (!cpseName.trim()) { toast.error('Enter CPSE name'); return }
    if (!file) { toast.error('Select a file'); return }
    setUploading(true)
    setError(null)
    setResult(null)
    try {
      const { data } = await uploadFile(cpseName.trim(), file)
      setResult(data)
      toast.success(`Uploaded ${data.inserted} records for ${data.cpse_name}`)
    } catch (e) {
      const msg = e.response?.data?.detail || e.message
      setError(msg)
      toast.error('Upload failed: ' + msg)
    } finally {
      setUploading(false)
    }
  }

  const reset = () => {
    setFile(null); setPreview([]); setPreviewHeaders([])
    setResult(null); setError(null)
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  return (
    <div className="max-w-3xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Upload CPSE Data</h1>
        <p className="text-gray-500 text-sm mt-0.5">
          Upload an Excel or CSV file for a CPSE. Required columns:{' '}
          <code className="bg-gray-100 px-1 rounded text-xs">material_code</code>,{' '}
          <code className="bg-gray-100 px-1 rounded text-xs">description</code>
        </p>
      </div>

      <div className="card p-6 space-y-5">
        {/* CPSE name */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">CPSE Name</label>
          <input
            type="text"
            className="input max-w-sm"
            placeholder="e.g. CPSE_A, BHEL, NTPC"
            value={cpseName}
            onChange={e => setCpseName(e.target.value)}
          />
        </div>

        {/* Drop zone */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Data File</label>
          <div
            onDrop={onDrop}
            onDragOver={e => e.preventDefault()}
            onClick={() => !file && fileInputRef.current?.click()}
            className={`border-2 border-dashed rounded-xl p-8 text-center transition-colors
              ${file ? 'border-primary-400 bg-primary-50' : 'border-gray-300 hover:border-primary-400 cursor-pointer bg-gray-50 hover:bg-primary-50'}`}
          >
            {file ? (
              <div className="flex items-center justify-center gap-3">
                <FileSpreadsheet size={28} className="text-primary-600" />
                <div className="text-left">
                  <p className="font-medium text-gray-900">{file.name}</p>
                  <p className="text-xs text-gray-500">{(file.size / 1024).toFixed(1)} KB</p>
                </div>
                <button onClick={e => { e.stopPropagation(); reset() }}
                  className="ml-2 p-1 hover:bg-red-100 rounded-full text-gray-400 hover:text-red-600 transition-colors">
                  <X size={16} />
                </button>
              </div>
            ) : (
              <>
                <UploadIcon size={32} className="text-gray-400 mx-auto mb-2" />
                <p className="text-gray-600 font-medium">Drop file here or click to browse</p>
                <p className="text-gray-400 text-xs mt-1">Accepts .xlsx, .xls, .csv</p>
              </>
            )}
          </div>
          <input ref={fileInputRef} type="file" accept=".xlsx,.xls,.csv" className="hidden"
            onChange={e => handleFile(e.target.files[0])} />
        </div>

        {/* Download sample template */}
        <p className="text-xs text-gray-500">
          Need a template?{' '}
          <a
            href="data:text/csv;charset=utf-8,material_code,description,uom,unit_price,annual_qty%0AA-000001,BOLT HEX M10X50 GR 8.8 ZINC PLATED,NOS,12.50,500"
            download="sample_template.csv"
            className="text-primary-600 underline hover:text-primary-700"
          >
            Download sample CSV template
          </a>
        </p>

        <button onClick={handleSubmit} disabled={uploading || !file || !cpseName} className="btn-primary">
          {uploading ? 'Uploading…' : <><UploadIcon size={16} /> Upload File</>}
        </button>
      </div>

      {/* Result */}
      {result && (
        <div className="card p-5 border-green-200 bg-green-50">
          <div className="flex items-start gap-3">
            <CheckCircle2 size={20} className="text-green-600 mt-0.5" />
            <div>
              <p className="font-semibold text-green-800">Upload successful for {result.cpse_name}</p>
              <ul className="text-sm text-green-700 mt-1 space-y-0.5">
                <li>Total rows: <b>{result.total_rows}</b></li>
                <li>Inserted: <b>{result.inserted}</b></li>
                <li>Skipped (duplicates): <b>{result.skipped}</b></li>
              </ul>
            </div>
          </div>
        </div>
      )}
      {error && (
        <div className="card p-5 border-red-200 bg-red-50">
          <div className="flex items-start gap-3">
            <AlertCircle size={20} className="text-red-600 mt-0.5" />
            <p className="text-red-800 text-sm">{error}</p>
          </div>
        </div>
      )}

      {/* Preview */}
      {preview.length > 0 && (
        <div className="card p-5">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">Preview (first 10 rows)</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead className="bg-gray-50">
                <tr>
                  {previewHeaders.map(h => (
                    <th key={h} className="px-3 py-2 text-left font-semibold text-gray-600 uppercase tracking-wide whitespace-nowrap">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {preview.map((row, i) => (
                  <tr key={i} className="hover:bg-gray-50">
                    {row.map((cell, j) => (
                      <td key={j} className="px-3 py-2 text-gray-700 max-w-xs truncate">{String(cell)}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
