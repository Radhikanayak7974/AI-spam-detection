import { useState, useCallback, useEffect } from 'react'
import {
  Inbox, RefreshCw, WifiOff, Download, CheckCircle,
  AlertCircle, Clock, BarChart2
} from 'lucide-react'
import EmailTable from '../components/EmailTable'
import GmailConnectCard from '../components/GmailConnectCard'
import EmptyState from '../components/EmptyState'
import useApi from '../hooks/useApi'
import { emailsAPI, authAPI, gmailAPI } from '../services/api'

function SyncStatsBar({ stats }) {
  if (!stats) return null
  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
      {[
        { label: 'Fetched',     value: stats.emails_fetched    ?? 0, color: 'brand'   },
        { label: 'Classified',  value: stats.emails_classified ?? 0, color: 'emerald' },
        { label: 'Spam',        value: stats.spam_detected     ?? 0, color: 'red'     },
        { label: 'Duration',    value: stats.duration ? `${stats.duration.toFixed(1)}s` : '—', color: 'slate' },
      ].map(({ label, value, color }) => (
        <div key={label} className="rounded-xl bg-slate-50 dark:bg-navy-700/40 px-3 py-2 text-center">
          <p className={`text-lg font-bold text-${color}-600 dark:text-${color}-400`}>{value}</p>
          <p className="text-[10px] text-slate-500 dark:text-slate-400 mt-0.5">{label}</p>
        </div>
      ))}
    </div>
  )
}

function SyncStatusBanner({ status, onDismiss }) {
  if (!status) return null
  const isSuccess = status.type === 'success'
  return (
    <div className={`flex items-start gap-3 p-3 rounded-xl border text-xs mb-4 ${
      isSuccess
        ? 'bg-emerald-50 border-emerald-200 text-emerald-800 dark:bg-emerald-900/20 dark:border-emerald-800/30 dark:text-emerald-300'
        : 'bg-red-50 border-red-200 text-red-800 dark:bg-red-900/20 dark:border-red-800/30 dark:text-red-300'
    }`}>
      {isSuccess
        ? <CheckCircle className="w-4 h-4 shrink-0 mt-0.5" />
        : <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
      }
      <span className="flex-1">{status.message}</span>
      <button onClick={onDismiss} className="shrink-0 opacity-60 hover:opacity-100 text-base leading-none">×</button>
    </div>
  )
}

export default function GmailInbox() {
  const { data: auth, refetch: refetchAuth }       = useApi(authAPI.status)
  const { data, loading, refetch: refetchEmails }  = useApi(emailsAPI.list)
  const { data: syncStatus, refetch: refetchStatus } = useApi(gmailAPI.syncStatus)

  const [syncing,       setSyncing]       = useState(false)
  const [syncResult,    setSyncResult]    = useState(null)  // { type, message, stats }
  const [syncProgress,  setSyncProgress]  = useState('')

  const emails     = data?.items || data || []
  const connected  = auth?.connected === true
  const lastSync   = syncStatus?.last_sync

  const handleSync = useCallback(async (fullSync = false) => {
    setSyncing(true)
    setSyncResult(null)
    setSyncProgress(fullSync ? 'Running full inbox sync…' : 'Checking for new emails…')

    try {
      const res = await gmailAPI.sync({ full: fullSync })
      const result = res.data?.data || {}
      const stats  = result.stats || result.sync || {}

      setSyncResult({
        type: 'success',
        message: result.message || 'Sync completed successfully',
        stats: {
          emails_fetched:    stats.emails_fetched    ?? 0,
          emails_classified: stats.emails_classified ?? 0,
          spam_detected:     stats.spam_detected     ?? 0,
          duration:          result.sync?.duration_seconds,
        },
      })

      // Refresh data
      await Promise.all([refetchEmails(), refetchAuth(), refetchStatus()])
    } catch (err) {
      setSyncResult({
        type: 'error',
        message: err.userMessage || err.message || 'Sync failed. Please try again.',
      })
    } finally {
      setSyncing(false)
      setSyncProgress('')
    }
  }, [refetchEmails, refetchAuth, refetchStatus])

  const handleDisconnect = useCallback(async () => {
    const { authAPI: aAPI } = await import('../services/api')
    await aAPI.logout()
    refetchAuth()
  }, [refetchAuth])

  // Handle OAuth redirect return (?connected=true or ?error=...)
  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    if (params.get('connected') === 'true') {
      setSyncResult({
        type: 'success',
        message: 'Gmail account connected successfully! Synchronizing inbox emails...',
      })
      refetchAuth().then(() => {
        handleSync(true)
      })
      window.history.replaceState({}, document.title, window.location.pathname)
    } else if (params.get('error')) {
      setSyncResult({
        type: 'error',
        message: `Connection failed: ${params.get('error')}`,
      })
      window.history.replaceState({}, document.title, window.location.pathname)
    }
  }, [handleSync, refetchAuth])

  // Periodic polling for new emails (every 30 seconds when connected)
  useEffect(() => {
    if (!connected) return
    const interval = setInterval(() => {
      // Background incremental check for new emails sent or received from phone/web
      gmailAPI.sync({ full: false })
        .then(() => {
          refetchEmails()
          refetchStatus()
        })
        .catch(() => {})
    }, 30000)

    return () => clearInterval(interval)
  }, [connected, refetchEmails, refetchStatus])

  return (
    <div className="space-y-6">
      {/* Not connected state */}
      {!connected && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <EmptyState
              icon={WifiOff}
              title="Gmail Not Connected"
              description="Connect your Gmail account to view and scan your inbox emails."
              action={
                <span className="text-xs text-slate-400 dark:text-slate-500 bg-slate-100 dark:bg-navy-700 px-3 py-1.5 rounded-lg">
                  Use the Connect Gmail card →
                </span>
              }
            />
          </div>
          <GmailConnectCard authStatus={{ connected: false }} />
        </div>
      )}

      {/* Connected state */}
      {connected && (
        <>
          {/* Sync notifications */}
          {syncResult && (
            <SyncStatusBanner
              status={syncResult}
              onDismiss={() => setSyncResult(null)}
            />
          )}

          {/* Sync stats row */}
          {syncResult?.stats && <SyncStatsBar stats={syncResult.stats} />}

          {/* Main inbox card */}
          <div className="card">
            <div className="flex items-center justify-between px-5 py-4 border-b border-slate-100 dark:border-navy-700/60 flex-wrap gap-3">
              <div className="flex items-center gap-2">
                <Inbox className="w-4.5 h-4.5 text-brand-500" style={{ width:'1.1rem', height:'1.1rem' }} />
                <div>
                  <h2 className="font-semibold text-slate-800 dark:text-slate-200 text-sm">Gmail Inbox</h2>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                    {data?.meta?.total ?? emails.length} emails total
                    {lastSync && (
                      <span className="ml-2 inline-flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {new Date(lastSync.started_at).toLocaleString()}
                      </span>
                    )}
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-2">
                {/* Incremental sync */}
                <button
                  onClick={() => handleSync(false)}
                  disabled={syncing}
                  className="btn-secondary text-xs gap-1.5"
                  title="Check for new emails (incremental)"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${syncing ? 'animate-spin' : ''}`} />
                  {syncing ? syncProgress || 'Syncing…' : 'Sync New'}
                </button>

                {/* Full sync */}
                <button
                  onClick={() => handleSync(true)}
                  disabled={syncing}
                  className="btn-primary text-xs gap-1.5"
                  title="Full inbox synchronization"
                >
                  <Download className="w-3.5 h-3.5" />
                  Full Sync
                </button>

                {/* Refresh display */}
                <button
                  onClick={() => { refetchEmails(); refetchStatus() }}
                  disabled={loading}
                  className="btn-ghost p-2"
                  title="Refresh list"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
                </button>
              </div>
            </div>

            {/* Syncing progress indicator */}
            {syncing && (
              <div className="px-5 py-3 bg-brand-50 dark:bg-brand-900/10 border-b border-brand-100 dark:border-brand-800/20 flex items-center gap-2 text-xs text-brand-700 dark:text-brand-300">
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                {syncProgress}
              </div>
            )}

            <div className="p-2">
              <EmailTable
                emails={emails}
                loading={loading}
                emptyTitle="Inbox is empty"
                emptyDescription="Click 'Full Sync' to fetch your real Gmail inbox messages."
              />
            </div>
          </div>

          {/* Sidebar: connection card + scheduler status */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2">
              {syncStatus?.last_sync && (
                <div className="card p-4">
                  <div className="flex items-center gap-2 mb-3">
                    <BarChart2 className="w-4 h-4 text-brand-500" />
                    <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-200">Last Sync Summary</h3>
                  </div>
                  <SyncStatsBar stats={{
                    emails_fetched:    syncStatus.last_sync.emails_fetched,
                    emails_classified: syncStatus.last_sync.emails_processed,
                    spam_detected:     syncStatus.last_sync.spam_detected,
                    duration:          syncStatus.last_sync.duration_seconds,
                  }} />
                  <p className="text-[10px] text-slate-400 dark:text-slate-500">
                    Status: <span className={`font-medium ${
                      syncStatus.last_sync.status === 'completed' ? 'text-emerald-500' : 'text-red-500'
                    }`}>{syncStatus.last_sync.status}</span>
                    {syncStatus.last_sync.error_message && (
                      <span className="ml-2 text-red-500">{syncStatus.last_sync.error_message}</span>
                    )}
                  </p>
                </div>
              )}
            </div>

            <GmailConnectCard
              authStatus={auth || { connected: false }}
              onSync={() => handleSync(false)}
              onDisconnect={handleDisconnect}
            />
          </div>
        </>
      )}
    </div>
  )
}
