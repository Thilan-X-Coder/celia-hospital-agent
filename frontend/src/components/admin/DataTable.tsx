import type { ReactNode } from 'react'
import { useMemo, useState } from 'react'
import EmptyState from './EmptyState'

const PAGE_SIZE = 10

export type Column<T> = {
  key: keyof T
  label: string
  sortable?: boolean
  render?: (row: T) => ReactNode
}

type DataTableProps<T> = {
  columns: Column<T>[]
  rows: T[]
  rowKey: (row: T) => string
  searchKeys: (keyof T)[]
  searchPlaceholder?: string
  statusKey?: keyof T
  statusOptions?: string[]
  emptyMessage: string
}

export default function DataTable<T>({
  columns,
  rows,
  rowKey,
  searchKeys,
  searchPlaceholder = 'Search...',
  statusKey,
  statusOptions,
  emptyMessage,
}: DataTableProps<T>) {
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [sortKey, setSortKey] = useState<keyof T | null>(null)
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc')
  const [page, setPage] = useState(1)

  const filtered = useMemo(() => {
    let result = rows

    if (statusKey && statusFilter !== 'all') {
      result = result.filter((row) => String(row[statusKey] ?? '') === statusFilter)
    }

    const query = search.trim().toLowerCase()
    if (query) {
      result = result.filter((row) =>
        searchKeys.some((key) => String(row[key] ?? '').toLowerCase().includes(query)),
      )
    }

    if (sortKey) {
      result = [...result].sort((a, b) => {
        const cmp = String(a[sortKey] ?? '').localeCompare(String(b[sortKey] ?? ''), undefined, {
          numeric: true,
        })
        return sortDir === 'asc' ? cmp : -cmp
      })
    }

    return result
  }, [rows, search, statusFilter, sortKey, sortDir, searchKeys, statusKey])

  const pageCount = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE))
  const currentPage = Math.min(page, pageCount)
  const pageRows = filtered.slice((currentPage - 1) * PAGE_SIZE, currentPage * PAGE_SIZE)

  function toggleSort(key: keyof T) {
    if (sortKey !== key) {
      setSortKey(key)
      setSortDir('asc')
    } else {
      setSortDir((dir) => (dir === 'asc' ? 'desc' : 'asc'))
    }
    setPage(1)
  }

  if (rows.length === 0) {
    return <EmptyState message={emptyMessage} />
  }

  return (
    <div>
      <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <input
          type="text"
          value={search}
          onChange={(e) => {
            setSearch(e.target.value)
            setPage(1)
          }}
          placeholder={searchPlaceholder}
          className="w-full rounded-full border border-cream px-4 py-2 text-sm text-primary outline-none focus:border-primary sm:max-w-xs"
        />
        {statusKey && statusOptions && (
          <select
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value)
              setPage(1)
            }}
            className="w-full rounded-full border border-cream px-4 py-2 text-sm text-primary outline-none focus:border-primary sm:w-auto"
          >
            <option value="all">All statuses</option>
            {statusOptions.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        )}
      </div>

      {filtered.length === 0 ? (
        <EmptyState message="No results match your search." />
      ) : (
        <>
          <div className="overflow-x-auto rounded-2xl border border-cream">
            <table className="w-full min-w-[640px] text-left text-sm">
              <thead className="bg-cream/50 text-xs font-semibold uppercase tracking-wide text-primary/60">
                <tr>
                  {columns.map((col) => (
                    <th key={String(col.key)} className="px-4 py-3">
                      {col.sortable ? (
                        <button
                          type="button"
                          onClick={() => toggleSort(col.key)}
                          className="flex items-center gap-1 hover:text-primary"
                        >
                          {col.label}
                          {sortKey === col.key && <span>{sortDir === 'asc' ? '↑' : '↓'}</span>}
                        </button>
                      ) : (
                        col.label
                      )}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {pageRows.map((row) => (
                  <tr key={rowKey(row)} className="border-t border-cream/70">
                    {columns.map((col) => (
                      <td key={String(col.key)} className="px-4 py-3 align-top text-primary">
                        {col.render ? col.render(row) : String(row[col.key] ?? '')}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="mt-4 flex items-center justify-between text-sm text-primary/70">
            <span>
              Page {currentPage} of {pageCount} &middot; {filtered.length} result
              {filtered.length === 1 ? '' : 's'}
            </span>
            <div className="flex gap-2">
              <button
                type="button"
                disabled={currentPage <= 1}
                onClick={() => setPage((p) => p - 1)}
                className="rounded-full border border-cream px-3 py-1 disabled:opacity-40"
              >
                Prev
              </button>
              <button
                type="button"
                disabled={currentPage >= pageCount}
                onClick={() => setPage((p) => p + 1)}
                className="rounded-full border border-cream px-3 py-1 disabled:opacity-40"
              >
                Next
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
