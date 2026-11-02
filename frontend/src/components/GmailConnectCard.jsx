import { useState } from 'react'
import {
  Mail, RefreshCw, LogOut, Wifi, WifiOff, Clock, User, ExternalLink, AlertCircle, X, KeyRound, Copy, Check
} from 'lucide-react'
import { authAPI } from '../services/api'

function formatDate(iso) {
  if (!iso) return null
  const d = new Date(iso)
  return d.toLocaleString('en-US', {
    month: 'short', day: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

/**
 * GmailConnectCard – Gmail OAuth connection UI.
 * Handles OAuth login flow with clear credential setup assistance.
 */
export default function GmailConnectCard({ authStatus, onConnect, onSync, onDisconnect }) {
  const [syncing, setSyncing] = useState(false)
  const [loading, setLoading] = useState(false)
  const [showConfigModal, setShowConfigModal] = useState(false)
  const [copied, setCopied] = useState(false)

  const connected = authStatus?.connected === true
  const user      = authStatus?.user
  const lastSync  = authStatus?.last_sync

  async function handleConnectClick() {
    if (onConnect) {
      onConnect()
      return
    }

    try {
      setLoading(true)
      const res = await authAPI.login()
      if (res.data?.data?.oauth_url) {
        window.location.href = res.data.data.oauth_url
      }
    } catch (err) {
      // If credentials not set up in .env yet, open setup instructions modal
      setShowConfigModal(true)
    } finally {
      setLoading(false)
    }
  }

  async function handleSync() {
    if (!onSync) return
    setSyncing(true)
    await onSync()
    setSyncing(false)
  }

  const sampleEnvText = `GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=http://localhost:5000/api/auth/callback`

  const handleCopyEnv = () => {
    navigator.clipboard.writeText(sampleEnvText)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  if (!connected) {
    return (
      <>
        <div className="card p-6 flex flex-col items-center text-center gap-5 relative overflow-hidden">
          {/* Background decoration */}
          <div className="absolute -top-8 -right-8 w-32 h-32 rounded-full bg-gradient-to-br from-brand-100 to-purple-100 dark:from-brand-900/20 dark:to-purple-900/20 opacity-50" />

          <div className="relative w-14 h-14 rounded-2xl bg-gradient-to-br from-brand-500 to-purple-600 flex items-center justify-center shadow-lg shadow-brand-500/20">
            <Mail className="w-7 h-7 text-white" />
          </div>

          <div className="relative">
            <h3 className="font-bold text-slate-800 dark:text-slate-200 text-lg">Connect Gmail</h3>
            <p className="text-sm text-slate-500 dark:text-slate-400 mt-1.5 max-w-xs">
              Connect your Gmail account to scan and detect spam messages in real-time.
            </p>
          </div>

          <button
            id="gmail-connect-btn"
            onClick={handleConnectClick}
            disabled={loading}
            className="relative btn-primary w-full justify-center py-3 gap-2.5 text-sm"
          >
            {loading ? (
              <RefreshCw className="w-4 h-4 animate-spin" />
            ) : (
              <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
                <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
                <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
                <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z" fill="#FBBC05"/>
                <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
              </svg>
            )}
            Connect with Google
          </button>

          <div className="relative flex items-center gap-1.5">
            <WifiOff className="w-3.5 h-3.5 text-slate-400" />
            <span className="text-xs text-slate-400 dark:text-slate-500">Google OAuth 2.0 Ready</span>
          </div>
        </div>

        {/* Credentials Setup Modal */}
        {showConfigModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fade-in">
            <div className="card w-full max-w-lg p-6 space-y-4 shadow-2xl relative border border-slate-200 dark:border-navy-700">
              <button
                onClick={() => setShowConfigModal(false)}
                className="absolute top-4 right-4 p-1.5 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
              >
                <X className="w-5 h-5" />
              </button>

              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-brand-50 dark:bg-brand-900/30 flex items-center justify-center text-brand-600 dark:text-brand-400">
                  <KeyRound className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-bold text-slate-900 dark:text-slate-100 text-base">
                    Google OAuth 2.0 Setup Required
                  </h3>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                    Google Cloud Client Credentials need to be specified in your `.env` file
                  </p>
                </div>
              </div>

              <div className="space-y-3 text-xs text-slate-600 dark:text-slate-300">
                <p>To enable real Gmail sync through Google OAuth 2.0:</p>
                <ol className="list-decimal pl-4 space-y-1.5">
                  <li>Visit the <strong>Google Cloud Console &rarr; APIs &amp; Services &rarr; Credentials</strong></li>
                  <li>Create an <strong>OAuth 2.0 Client ID</strong> (Web application)</li>
                  <li>Add authorized redirect URI: <code className="bg-slate-100 dark:bg-navy-700 px-1.5 py-0.5 rounded text-brand-600 dark:text-brand-400 font-mono">http://localhost:5000/api/auth/callback</code></li>
                  <li>Copy your Client ID and Client Secret into your project's <code className="font-mono">.env</code> file</li>
                </ol>
              </div>

              <div className="relative">
                <div className="p-3 rounded-xl bg-slate-900 text-slate-200 font-mono text-xs overflow-x-auto">
                  <pre>{sampleEnvText}</pre>
                </div>
                <button
                  onClick={handleCopyEnv}
                  className="absolute top-2 right-2 px-2 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded text-[11px] flex items-center gap-1"
                >
                  {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                  {copied ? 'Copied!' : 'Copy'}
                </button>
              </div>

              <div className="flex justify-end pt-2">
                <button
                  onClick={() => setShowConfigModal(false)}
                  className="btn-primary text-xs py-2 px-4"
                >
                  Got It
                </button>
              </div>
            </div>
          </div>
        )}
      </>
    )
  }

  return (
    <div className="card p-5 flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-emerald-50 dark:bg-emerald-900/20 flex items-center justify-center">
            <Wifi className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
          </div>
          <div>
            <p className="font-semibold text-slate-800 dark:text-slate-200 text-sm">Gmail Connected</p>
            <span className="badge-connected text-[10px] font-semibold px-1.5 py-0.5 rounded-full bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400">
              ● Active
            </span>
          </div>
        </div>
        <ExternalLink className="w-4 h-4 text-slate-400" />
      </div>

      {user && (
        <div className="flex items-center gap-2 py-2 px-3 rounded-xl bg-slate-50 dark:bg-navy-700/40">
          {user.picture
            ? <img src={user.picture} alt="avatar" className="w-7 h-7 rounded-full" />
            : <div className="w-7 h-7 rounded-full bg-brand-100 flex items-center justify-center">
                <User className="w-3.5 h-3.5 text-brand-600" />
              </div>
          }
          <div className="min-w-0">
            <p className="text-xs font-medium text-slate-800 dark:text-slate-200 truncate">{user.name || user.email}</p>
            <p className="text-[10px] text-slate-500 truncate">{user.email}</p>
          </div>
        </div>
      )}

      {lastSync && (
        <div className="flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400">
          <Clock className="w-3.5 h-3.5" />
          Last sync: {formatDate(lastSync)}
        </div>
      )}

      <div className="flex gap-2">
        <button
          id="gmail-sync-btn"
          onClick={handleSync}
          disabled={syncing}
          className="btn-primary flex-1 justify-center text-xs py-2"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${syncing ? 'animate-spin' : ''}`} />
          {syncing ? 'Syncing…' : 'Sync Now'}
        </button>
        <button
          id="gmail-disconnect-btn"
          onClick={onDisconnect}
          className="btn-secondary text-xs py-2 px-3"
        >
          <LogOut className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  )
}
