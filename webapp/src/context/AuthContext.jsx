import { createContext, useContext, useEffect, useMemo, useState } from 'react'
import { api } from '../lib/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem('pot_token') || '')
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(Boolean(token))

  useEffect(() => {
    let cancelled = false
    async function bootstrap() {
      if (!token) {
        setLoading(false)
        return
      }
      try {
        const me = await api('/api/auth/me', {}, token)
        if (!cancelled) setUser(me.user)
      } catch (_err) {
        if (!cancelled) {
          setToken('')
          setUser(null)
          localStorage.removeItem('pot_token')
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    bootstrap()
    return () => {
      cancelled = true
    }
  }, [token])

  const login = async (email, password) => {
    const out = await api('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password })
    })
    setToken(out.token)
    setUser(out.user)
    localStorage.setItem('pot_token', out.token)
    return out
  }

  const register = async (payload) => {
    const out = await api('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify(payload)
    })
    setToken(out.token)
    setUser(out.user)
    localStorage.setItem('pot_token', out.token)
    return out
  }

  const updateProfile = async (payload) => {
    const out = await api('/api/profile/me', {
      method: 'PUT',
      body: JSON.stringify(payload)
    }, token)
    setUser(out.user)
    return out
  }

  const logout = () => {
    setToken('')
    setUser(null)
    localStorage.removeItem('pot_token')
  }

  const value = useMemo(() => ({ token, user, loading, login, register, updateProfile, logout }), [token, user, loading])
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used in AuthProvider')
  return ctx
}
