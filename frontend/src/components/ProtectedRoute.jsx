import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { ShieldCheck, Loader2 } from 'lucide-react'

export default function ProtectedRoute({ children }) {
  const { isAuthenticated, loading } = useAuth()
  const location = useLocation()

  if (loading) {
    return (
      <div className="min-h-screen bg-[#070A13] flex flex-col items-center justify-center text-white">
        <div className="relative flex items-center justify-center">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-brand-600 to-purple-600 animate-pulse flex items-center justify-center shadow-lg shadow-purple-500/20">
            <ShieldCheck className="w-8 h-8 text-white" />
          </div>
          <Loader2 className="w-20 h-20 text-purple-400 animate-spin absolute" />
        </div>
        <p className="mt-4 text-sm font-medium text-slate-400">Verifying security session...</p>
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  return children
}

