import { useState } from 'react'
import { clearAdminToken, getAdminToken, setAdminToken } from './adminApi'

/** Small auth hook for the admin dashboard: token lives in sessionStorage (cleared on
 * logout or any 401) and in React state so components re-render when it changes. */
export function useAdminAuth() {
  const [token, setToken] = useState<string | null>(() => getAdminToken())

  const login = (newToken: string) => {
    setAdminToken(newToken)
    setToken(newToken)
  }

  const logout = () => {
    clearAdminToken()
    setToken(null)
  }

  return { token, isAuthed: !!token, login, logout }
}
