/**
 * useApi – generic hook for async data fetching.
 * Usage:
 *   const { data, loading, error, refetch } = useApi(dashboardAPI.stats)
 */
import { useState, useEffect, useCallback, useRef } from 'react'

export default function useApi(apiFn, deps = [], autoFetch = true) {
  const [data,    setData]    = useState(null)
  const [loading, setLoading] = useState(autoFetch)
  const [error,   setError]   = useState(null)
  const mountedRef = useRef(true)

  const fetch = useCallback(async (...args) => {
    setLoading(true)
    setError(null)
    try {
      const res = await apiFn(...args)
      if (mountedRef.current) {
        setData(res.data?.data ?? res.data)
      }
    } catch (err) {
      if (mountedRef.current) {
        setError(err.userMessage || err.message || 'Request failed')
      }
    } finally {
      if (mountedRef.current) setLoading(false)
    }
  }, deps) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    mountedRef.current = true
    if (autoFetch) fetch()
    return () => { mountedRef.current = false }
  }, [fetch]) // eslint-disable-line react-hooks/exhaustive-deps

  return { data, loading, error, refetch: fetch }
}
