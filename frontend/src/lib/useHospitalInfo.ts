import { useEffect, useState } from 'react'
import { getHospitalInfo } from './api'
import type { HospitalResponse } from './api'

export type HospitalInfoState =
  | { status: 'loading' }
  | { status: 'success'; data: HospitalResponse }
  | { status: 'error'; message: string }

/** Shared fetch hook: every component that needs live hospital data uses this. */
export function useHospitalInfo(): HospitalInfoState {
  const [state, setState] = useState<HospitalInfoState>({ status: 'loading' })

  useEffect(() => {
    let cancelled = false

    getHospitalInfo()
      .then((data) => {
        if (!cancelled) setState({ status: 'success', data })
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setState({
            status: 'error',
            message: err instanceof Error ? err.message : 'Unknown error',
          })
        }
      })

    return () => {
      cancelled = true
    }
  }, [])

  return state
}

/** "A, B, C" -> ["A", "B", "C"], safe for null/undefined. */
export function splitCommaList(value: string | null | undefined): string[] {
  if (!value) return []
  return value
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean)
}
