import { useCallback, useEffect, useState } from 'react'
import { Navigate } from 'react-router-dom'
import type {
  AdminAppointment,
  AdminConversation,
  AdminDoctor,
  AdminSummaryResponse,
} from '../lib/adminApi'
import {
  adminLogout,
  downloadAdminReport,
  getAdminAppointments,
  getAdminConversations,
  getAdminDoctors,
  getAdminSummary,
} from '../lib/adminApi'
import { ApiError } from '../lib/api'
import { formatLkr } from '../lib/format'
import { useAdminAuth } from '../lib/useAdminAuth'
import KpiCard from '../components/admin/KpiCard'
import AppointmentsTab from '../components/admin/AppointmentsTab'
import ConversationsTab from '../components/admin/ConversationsTab'
import DoctorsTab from '../components/admin/DoctorsTab'

type DashboardState =
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | {
      status: 'success'
      summary: AdminSummaryResponse
      appointments: AdminAppointment[]
      conversations: AdminConversation[]
      doctors: AdminDoctor[]
    }

type Tab = 'appointments' | 'conversations' | 'doctors'

const TABS: { key: Tab; label: string }[] = [
  { key: 'appointments', label: 'Appointments' },
  { key: 'conversations', label: 'Conversations' },
  { key: 'doctors', label: 'Doctors & availability' },
]

export default function AdminDashboardPage() {
  const { isAuthed, logout } = useAdminAuth()
  const [state, setState] = useState<DashboardState>({ status: 'loading' })
  const [tab, setTab] = useState<Tab>('appointments')
  const [downloading, setDownloading] = useState(false)
  const [refreshing, setRefreshing] = useState(false)

  const load = useCallback(async () => {
    try {
      const [summary, appointments, conversations, doctors] = await Promise.all([
        getAdminSummary(),
        getAdminAppointments(),
        getAdminConversations(),
        getAdminDoctors(),
      ])
      setState({ status: 'success', summary, appointments, conversations, doctors })
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        logout()
        return
      }
      setState({
        status: 'error',
        message: err instanceof Error ? err.message : 'Could not load the dashboard.',
      })
    }
  }, [logout])

  useEffect(() => {
    if (isAuthed) load()
  }, [isAuthed, load])

  if (!isAuthed) {
    return <Navigate to="/admin" replace />
  }

  async function handleRefresh() {
    setRefreshing(true)
    await load()
    setRefreshing(false)
  }

  async function handleLogout() {
    try {
      await adminLogout()
    } catch {
      // already unauthenticated either way - still clear locally
    }
    logout()
  }

  async function handleDownload() {
    setDownloading(true)
    try {
      await downloadAdminReport()
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        logout()
      }
    } finally {
      setDownloading(false)
    }
  }

  return (
    <div className="mx-auto max-w-6xl px-4 py-8">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-bold text-primary">Dashboard</h1>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={handleRefresh}
            disabled={refreshing}
            className="rounded-full border border-cream px-4 py-2 text-sm font-semibold text-primary disabled:opacity-50"
          >
            {refreshing ? 'Refreshing...' : 'Refresh'}
          </button>
          <button
            type="button"
            onClick={handleDownload}
            disabled={downloading}
            className="rounded-full bg-accent px-4 py-2 text-sm font-semibold text-primary disabled:opacity-50"
          >
            {downloading ? 'Preparing...' : 'Download Excel report'}
          </button>
          <button
            type="button"
            onClick={handleLogout}
            className="rounded-full bg-primary px-4 py-2 text-sm font-semibold text-white"
          >
            Log out
          </button>
        </div>
      </div>

      {state.status === 'loading' && <p className="mt-8 text-primary/70">Loading dashboard...</p>}

      {state.status === 'error' && (
        <div className="mt-8 rounded-2xl border border-accent/30 bg-cream p-6 text-center">
          <p className="font-semibold text-primary">Can't load the dashboard right now</p>
          <p className="mt-1 text-sm text-primary/70">{state.message}</p>
        </div>
      )}

      {state.status === 'success' && (
        <>
          <div className="mt-6 grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6">
            <KpiCard label="Conversations" value={String(state.summary.total_conversations)} />
            <KpiCard label="Booked" value={String(state.summary.booked_conversations)} />
            <KpiCard
              label="Conversion"
              value={`${Math.round(state.summary.conversion_rate * 100)}%`}
            />
            <KpiCard label="Today's appointments" value={String(state.summary.todays_appointments)} />
            <KpiCard label="Upcoming appointments" value={String(state.summary.upcoming_appointments)} />
            <KpiCard label="Total revenue" value={formatLkr(state.summary.total_revenue_lkr)} />
          </div>

          <div className="mt-8 flex gap-2 border-b border-cream">
            {TABS.map((t) => (
              <button
                key={t.key}
                type="button"
                onClick={() => setTab(t.key)}
                className={`rounded-t-xl px-4 py-2 text-sm font-semibold ${
                  tab === t.key
                    ? 'bg-cream text-primary'
                    : 'text-primary/60 hover:text-primary'
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>

          <div className="mt-6">
            {tab === 'appointments' && <AppointmentsTab appointments={state.appointments} />}
            {tab === 'conversations' && <ConversationsTab conversations={state.conversations} />}
            {tab === 'doctors' && <DoctorsTab doctors={state.doctors} />}
          </div>
        </>
      )}
    </div>
  )
}
