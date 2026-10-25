import { useState } from 'react'
import type { FormEvent } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { adminLogin } from '../lib/adminApi'
import { ApiError } from '../lib/api'
import { useAdminAuth } from '../lib/useAdminAuth'

export default function AdminLoginPage() {
  const { isAuthed, login } = useAdminAuth()
  const navigate = useNavigate()
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  if (isAuthed) {
    return <Navigate to="/admin/dashboard" replace />
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      const { token } = await adminLogin(password)
      login(token)
      navigate('/admin/dashboard', { replace: true })
    } catch (err) {
      if (err instanceof ApiError && err.status === 503) {
        setError('Admin is not configured. Ask a developer to set ADMIN_PASSWORD in backend/.env.')
      } else if (err instanceof ApiError && err.status === 401) {
        setError('Incorrect password.')
      } else {
        setError('Could not reach the Celia backend. Please try again.')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="mx-auto flex max-w-sm flex-col items-center px-4 py-16">
      <h1 className="text-2xl font-bold text-primary">Staff login</h1>
      <p className="mt-1 text-center text-sm text-primary/70">
        Hospital staff only. This page is not linked from the main navigation.
      </p>

      <form onSubmit={handleSubmit} className="mt-8 w-full">
        <label htmlFor="admin-password" className="text-xs font-semibold uppercase tracking-wide text-primary/50">
          Password
        </label>
        <input
          id="admin-password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          autoFocus
          required
          className="mt-1 w-full rounded-full border border-cream px-4 py-3 text-sm text-primary outline-none focus:border-primary"
        />

        {error && (
          <p className="mt-3 rounded-2xl border border-accent/30 bg-cream p-3 text-center text-sm text-primary">
            {error}
          </p>
        )}

        <button
          type="submit"
          disabled={loading || password.length === 0}
          className="mt-6 w-full rounded-full bg-primary px-6 py-3 text-sm font-semibold text-white disabled:opacity-50"
        >
          {loading ? 'Checking...' : 'Log in'}
        </button>
      </form>
    </div>
  )
}
