/**
 * Typed client for the Celia backend API (see CLAUDE.md "API contract").
 */

export type HealthResponse = {
  status: string
  model: string
}

export type HospitalResponse = {
  name: string
  address: string
  phone: string
  email: string | null
  emergency_number: string
  opening_hours: string | null
  visiting_hours: string | null
  departments: string | null
  facilities: string | null
  what_to_bring: string | null
  payment_methods: string | null
}

export type ChatStartResponse = {
  session_id: string
  greeting: string
}

export type BookingOut = {
  appointment_id: string
  invoice_no: string
  doctor: string
  speciality: string
  date: string
  time: string
  fee_lkr: number
}

export type ChatResponse = {
  reply: string
  booking: BookingOut | null
  invoice_url: string | null
  conversation_ended: boolean
}

export type ChatEndResponse = {
  saved: boolean
  summary: string | null
}

const BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

/** Turn the relative `invoice_url` from a chat response into a fetchable/openable URL. */
export function getFullInvoiceUrl(invoiceUrl: string): string {
  return `${BASE_URL}${invoiceUrl}`
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })
  if (!res.ok) {
    const body = await res.json().catch(() => null)
    throw new Error(body?.detail ?? `Request failed: ${res.status}`)
  }
  return res.json()
}

export const getHealth = () => request<HealthResponse>('/api/health')

export const getHospitalInfo = () => request<HospitalResponse>('/api/hospital')

export const startChat = () =>
  request<ChatStartResponse>('/api/chat/start', { method: 'POST' })

export const sendMessage = (session_id: string, message: string) =>
  request<ChatResponse>('/api/chat', {
    method: 'POST',
    body: JSON.stringify({ session_id, message }),
  })

export const endChat = (session_id: string) =>
  request<ChatEndResponse>('/api/chat/end', {
    method: 'POST',
    body: JSON.stringify({ session_id }),
  })
