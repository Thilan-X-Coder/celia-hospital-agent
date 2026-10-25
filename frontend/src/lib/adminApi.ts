/**
 * Typed client for the admin dashboard API (see CLAUDE.md "Admin API contract").
 * Kept separate from lib/api.ts because every call here needs a Bearer token and
 * must log the admin out automatically on a 401.
 */
import { ApiError } from './api'

const BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'
const TOKEN_KEY = 'celia_admin_token'

export function getAdminToken(): string | null {
  try {
    return sessionStorage.getItem(TOKEN_KEY)
  } catch {
    return null
  }
}

export function setAdminToken(token: string): void {
  try {
    sessionStorage.setItem(TOKEN_KEY, token)
  } catch {
    // sessionStorage can be unavailable (private mode); the session just won't persist.
  }
}

export function clearAdminToken(): void {
  try {
    sessionStorage.removeItem(TOKEN_KEY)
  } catch {
    // nothing to do
  }
}

export type AdminLoginResponse = {
  token: string
  expires_in_hours: number
}

export type AdminSummaryResponse = {
  total_conversations: number
  booked_conversations: number
  conversion_rate: number
  todays_appointments: number
  total_revenue_lkr: number
  upcoming_appointments: number
}

export type AdminAppointment = {
  appointment_id: string
  patient_name: string
  phone_masked: string
  doctor: string
  speciality: string
  date: string
  time: string
  status: string
  reason: string | null
  invoice_no: string | null
  invoice_url: string | null
}

export type AdminConversation = {
  conversation_id: string | null
  date: string | null
  time: string | null
  patient_name: string | null
  phone_masked: string | null
  topics: string | null
  booking_status: string | null
  doctor: string | null
  speciality: string | null
  appointment_date: string | null
  appointment_time: string | null
  invoice_no: string | null
  summary: string | null
}

export type AdminDoctor = {
  doctor: string
  speciality: string
  fee: number
  working_days: string
  free_slots: number
  booked_slots: number
}

async function adminRequest<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = getAdminToken()
  const res = await fetch(`${BASE_URL}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...init.headers,
    },
  })
  if (res.status === 401) {
    clearAdminToken()
  }
  if (!res.ok) {
    const body = await res.json().catch(() => null)
    throw new ApiError(res.status, body?.detail ?? `Admin request failed: ${res.status}`)
  }
  return res.json()
}

export const adminLogin = (password: string) =>
  adminRequest<AdminLoginResponse>('/api/admin/login', {
    method: 'POST',
    body: JSON.stringify({ password }),
  })

export const adminLogout = () => adminRequest<{ ok: boolean }>('/api/admin/logout', { method: 'POST' })

export const getAdminSummary = () => adminRequest<AdminSummaryResponse>('/api/admin/summary')

export const getAdminAppointments = () => adminRequest<AdminAppointment[]>('/api/admin/appointments')

export const getAdminConversations = () => adminRequest<AdminConversation[]>('/api/admin/conversations')

export const getAdminDoctors = () => adminRequest<AdminDoctor[]>('/api/admin/doctors')

/** The download endpoint can't be a plain <a href> - it needs the Bearer token, so we
 * fetch it ourselves and save the result as a Blob. */
export async function downloadAdminReport(): Promise<void> {
  const token = getAdminToken()
  const res = await fetch(`${BASE_URL}/api/admin/report.xlsx`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  })
  if (res.status === 401) {
    clearAdminToken()
    throw new ApiError(401, 'Your admin session has expired. Please log in again.')
  }
  if (!res.ok) {
    const body = await res.json().catch(() => null)
    throw new ApiError(res.status, body?.detail ?? 'Could not download the report')
  }
  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'conversations.xlsx'
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}
