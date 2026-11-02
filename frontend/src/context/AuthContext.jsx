import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { userAuthAPI } from '../services/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [token, setToken] = useState(() => {
    return localStorage.getItem('spamguard_token') || sessionStorage.getItem('spamguard_token') || null
  })
  const [loading, setLoading] = useState(true)

  // Validate session on mount
  const checkAuth = useCallback(async () => {
    const activeToken = localStorage.getItem('spamguard_token') || sessionStorage.getItem('spamguard_token')
    if (!activeToken) {
      setUser(null)
      setLoading(false)
      return
    }

    try {
      const res = await userAuthAPI.me()
      if (res.data?.data?.authenticated && res.data.data.user) {
        setUser(res.data.data.user)
      } else {
        // Token invalid
        localStorage.removeItem('spamguard_token')
        sessionStorage.removeItem('spamguard_token')
        setUser(null)
        setToken(null)
      }
    } catch (err) {
      localStorage.removeItem('spamguard_token')
      sessionStorage.removeItem('spamguard_token')
      setUser(null)
      setToken(null)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    checkAuth()
  }, [checkAuth])

  const login = async (email, password, remember = false) => {
    const res = await userAuthAPI.login({ email, password, remember })
    const { token: authToken, user: userData } = res.data.data

    if (remember) {
      localStorage.setItem('spamguard_token', authToken)
      sessionStorage.removeItem('spamguard_token')
    } else {
      sessionStorage.setItem('spamguard_token', authToken)
      localStorage.removeItem('spamguard_token')
    }

    setToken(authToken)
    setUser(userData)
    return userData
  }

  const register = async (name, email, password) => {
    const res = await userAuthAPI.register({ name, email, password })
    return res.data
  }

  const logout = async () => {
    try {
      await userAuthAPI.logout()
    } catch (err) {
      // Ignore network errors during logout
    } finally {
      localStorage.removeItem('spamguard_token')
      sessionStorage.removeItem('spamguard_token')
      setUser(null)
      setToken(null)
    }
  }

  const value = {
    user,
    token,
    isAuthenticated: Boolean(user && token),
    loading,
    login,
    register,
    logout,
    refetchUser: checkAuth,
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

