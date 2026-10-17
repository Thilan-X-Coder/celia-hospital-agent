import { useEffect, useState } from 'react'
import { getHealth, getHospitalInfo } from '../lib/api'
import type { HealthResponse, HospitalResponse } from '../lib/api'

type Status =
  | { kind: 'loading' }
  | { kind: 'success'; health: HealthResponse; hospital: HospitalResponse }
  | { kind: 'error'; message: string }

export default function HealthCheckPage() {
  const [status, setStatus] = useState<Status>({ kind: 'loading' })

  useEffect(() => {
    let cancelled = false

    Promise.all([getHealth(), getHospitalInfo()])
      .then(([health, hospital]) => {
        if (!cancelled) setStatus({ kind: 'success', health, hospital })
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setStatus({
            kind: 'error',
            message: err instanceof Error ? err.message : 'Unknown error',
          })
        }
      })

    return () => {
      cancelled = true
    }
  }, [])

  return (
    <main className="flex min-h-screen items-center justify-center bg-white p-6 font-sans">
      {status.kind === 'loading' && <p className="text-primary">Checking the Celia backend...</p>}

      {status.kind === 'error' && (
        <div className="max-w-md rounded-2xl border border-accent/30 bg-cream p-6 text-center shadow-sm">
          <p className="mb-2 text-lg font-semibold text-primary">Can't reach the Celia backend</p>
          <p className="text-sm text-primary/80">
            Make sure the API server is running on{' '}
            <code className="rounded bg-white px-1.5 py-0.5">http://localhost:8000</code>.
          </p>
          <p className="mt-3 text-xs text-primary/60">{status.message}</p>
        </div>
      )}

      {status.kind === 'success' && (
        <div className="max-w-md rounded-2xl bg-cream p-8 text-center shadow-sm">
          <h1 className="text-2xl font-bold text-primary">{status.hospital.name}</h1>
          <p className="mt-1 text-sm text-primary/70">
            {status.hospital.phone} &middot; Emergency: {status.hospital.emergency_number}
          </p>
          <span className="mt-4 inline-block rounded-full bg-success px-3 py-1 text-xs font-semibold text-white">
            API: {status.health.status} ({status.health.model})
          </span>
        </div>
      )}
    </main>
  )
}
