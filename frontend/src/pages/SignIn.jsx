import { useState } from 'react'
import { Link, useNavigate, useLocation, Navigate } from 'react-router-dom'
import { Zap, Mail, Lock, Eye, EyeOff, ArrowRight, AlertCircle, CheckCircle2, ShieldCheck, Loader2 } from 'lucide-react'
import { useAuth } from '../context/AuthContext'

export default function SignIn() {
  const navigate = useNavigate()
  const location = useLocation()
  const { login, isAuthenticated } = useAuth()

  // If already logged in, redirect directly to dashboard
  if (isAuthenticated) {
    return <Navigate to="/overview" replace />
  }

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [remember, setRemember] = useState(true)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [successMsg, setSuccessMsg] = useState(location.state?.message || '')

  const from = location.state?.from?.pathname || '/overview'

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setSuccessMsg('')

    if (!email.trim() || !password.trim()) {
      setError('Please fill in both your email address and password.')
      return
    }

    setLoading(true)
    try {
      await login(email, password, remember)
      navigate(from, { replace: true })
    } catch (err) {
      setError(err.userMessage || 'Invalid email or password. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  // Quick fill helper for testing
  const handleQuickFillDemo = () => {
    setEmail('admin@spamguard.io')
    setPassword('SecurePassword123')
    setError('')
  }

  return (
    <div className="min-h-screen bg-[#070A13] text-slate-100 flex flex-col justify-center py-12 sm:px-6 lg:px-8 relative overflow-hidden font-sans">
      {/* Background ambient gradient glow */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[450px] bg-gradient-to-tr from-purple-700/20 via-blue-600/15 to-transparent blur-3xl pointer-events-none rounded-full" />

      <div className="sm:mx-auto sm:w-full sm:max-w-md relative z-10 px-4">
        {/* Logo */}
        <div className="text-center">
          <Link to="/" className="inline-flex items-center gap-3 group">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-brand-500 via-purple-600 to-indigo-600 flex items-center justify-center shadow-lg shadow-purple-500/25 group-hover:scale-105 transition-transform duration-300">
              <Zap className="w-6 h-6 text-white" />
            </div>
            <div className="text-left">
              <span className="text-2xl font-extrabold tracking-tight text-white">SpamGuard</span>
              <span className="text-xs ml-1.5 font-bold text-purple-400 uppercase tracking-widest px-2 py-0.5 rounded bg-purple-500/10 border border-purple-500/20">
                AI
              </span>
            </div>
          </Link>
          <h2 className="mt-6 text-2xl sm:text-3xl font-bold tracking-tight text-white">
            Welcome back
          </h2>
          <p className="mt-2 text-sm text-slate-400">
            Sign in to access your AI-secured email inbox & dashboard
          </p>
        </div>

        {/* Card Form */}
        <div className="mt-8 rounded-2xl bg-[#0B0F1D]/90 border border-slate-800/90 p-6 sm:p-8 shadow-2xl backdrop-blur-xl relative">
          {/* Success banner if redirected from sign up */}
          {successMsg && (
            <div className="mb-6 p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/25 text-emerald-300 text-sm flex items-center gap-2.5">
              <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
              <span>{successMsg}</span>
            </div>
          )}

          {/* Error banner */}
          {error && (
            <div className="mb-6 p-3.5 rounded-xl bg-red-500/10 border border-red-500/25 text-red-300 text-sm flex items-center gap-2.5">
              <AlertCircle className="w-5 h-5 text-red-400 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Email Field */}
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-2">
                Email Address
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-500">
                  <Mail className="w-4 h-4" />
                </div>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@company.com"
                  className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-slate-900/80 border border-slate-800 focus:border-purple-500 focus:ring-1 focus:ring-purple-500 text-slate-100 placeholder-slate-500 text-sm outline-none transition-all"
                />
              </div>
            </div>

            {/* Password Field */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300">
                  Password
                </label>
              </div>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-500">
                  <Lock className="w-4 h-4" />
                </div>
                <input
                  type={showPassword ? 'text' : 'password'}
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="w-full pl-10 pr-11 py-2.5 rounded-xl bg-slate-900/80 border border-slate-800 focus:border-purple-500 focus:ring-1 focus:ring-purple-500 text-slate-100 placeholder-slate-500 text-sm outline-none transition-all"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-slate-400 hover:text-slate-200"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {/* Remember Me */}
            <div className="flex items-center justify-between">
              <label className="flex items-center gap-2 cursor-pointer text-sm text-slate-400">
                <input
                  type="checkbox"
                  checked={remember}
                  onChange={(e) => setRemember(e.target.checked)}
                  className="w-4 h-4 rounded bg-slate-900 border-slate-700 text-purple-600 focus:ring-purple-500 focus:ring-offset-0"
                />
                Remember me for 30 days
              </label>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 px-4 rounded-xl font-semibold text-white bg-gradient-to-r from-brand-600 via-purple-600 to-indigo-600 hover:from-brand-500 hover:to-indigo-500 shadow-lg shadow-purple-600/25 hover:shadow-purple-600/40 disabled:opacity-50 transition-all flex items-center justify-center gap-2 text-sm"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Authenticating...
                </>
              ) : (
                <>
                  Sign In
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          {/* Quick Demo Credential Fill */}
          <div className="mt-6 pt-5 border-t border-slate-800 text-center">
            <button
              type="button"
              onClick={handleQuickFillDemo}
              className="text-xs text-purple-400 hover:text-purple-300 font-medium transition-colors"
            >
              Fill Demo Account (`admin@spamguard.io`)
            </button>
          </div>
        </div>

        {/* Link to Sign Up */}
        <p className="mt-6 text-center text-sm text-slate-400">
          Don't have an account yet?{' '}
          <Link to="/register" className="font-semibold text-purple-400 hover:text-purple-300 transition-colors">
            Create an account
          </Link>
        </p>
      </div>
    </div>
  )
}
