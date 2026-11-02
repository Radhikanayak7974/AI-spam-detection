import { useState, useCallback } from 'react'
import {
  Mail, ShieldAlert, ShieldCheck, Clock, Wifi, BarChart3,
  RefreshCw, Zap, AlertTriangle, Brain, Download, CheckCircle
} from 'lucide-react'
import StatisticCard from '../components/StatisticCard'
import ChartCard from '../components/ChartCard'
import GmailConnectCard from '../components/GmailConnectCard'
import EmailTable from '../components/EmailTable'
import StatusBadge from '../components/StatusBadge'
import useApi from '../hooks/useApi'
import { dashboardAPI, authAPI, gmailAPI, emailsAPI } from '../services/api'

export default function Overview() {
  const { data: stats,  loading: statsLoading,  refetch: refetchStats }  = useApi(dashboardAPI.stats)
  const { data: auth,   loading: authLoading,   refetch: refetchAuth }   = useApi(authAPI.status)
  const { data: recent, loading: recentLoading }                         = useApi(dashboardAPI.recentActivity)
  const { data: emailData, loading: emailsLoading, refetch: refetchEmails } = useApi(emailsAPI.list)

  const [syncing,    setSyncing]    = useState(false)
  const [syncMsg,    setSyncMsg]    = useState(null)
  const [connecting, setConnecting] = useState(false)

  const s = stats || {}
  const emails = emailData?.items || emailData || []

  const handleSync = useCallback(async () => {
    setSyncing(true)
    setSyncMsg(null)
    try {
      const res = await gmailAPI.sync({ full: false })
      const result = res.data?.data || {}
      setSyncMsg({ type: 'success', text: result.message || 'Sync complete' })
      await Promise.all([refetchStats(), refetchAuth(), refetchEmails()])
    } catch (err) {
      setSyncMsg({ type: 'error', text: err.userMessage || 'Sync failed' })
    } finally {
      setSyncing(false)
    }
  }, [refetchStats, refetchAuth, refetchEmails])

  const handleFullSync = useCallback(async () => {
    setSyncing(true)
    setSyncMsg(null)
    try {
      const res = await gmailAPI.sync({ full: true })
      const result = res.data?.data || {}
      setSyncMsg({ type: 'success', text: result.message || 'Full sync complete' })
      await Promise.all([refetchStats(), refetchAuth(), refetchEmails()])
    } catch (err) {
      setSyncMsg({ type: 'error', text: err.userMessage || 'Full sync failed' })
    } finally {
      setSyncing(false)
    }
  }, [refetchStats, refetchAuth, refetchEmails])

  const handleConnect = useCallback(async () => {
    setConnecting(true)
    try {
      const res = await authAPI.login()
      if (res.data?.data?.oauth_url) {
        window.location.href = res.data.data.oauth_url
      }
    } catch (err) {
      // OAuth not configured — GmailConnectCard shows the modal
    } finally {
      setConnecting(false)
    }
  }, [])

  const handleDisconnect = useCallback(async () => {
    await authAPI.logout()
    refetchAuth()
    refetchStats()
  }, [refetchAuth, refetchStats])

  return (
    <div className="space-y-6">
      {/* Sync notification banner */}
      {syncMsg && (
        <div className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs border ${
          syncMsg.type === 'success'
            ? 'bg-emerald-50 border-emerald-200 text-emerald-800 dark:bg-emerald-900/20 dark:border-emerald-700/30 dark:text-emerald-300'
            : 'bg-red-50 border-red-200 text-red-800 dark:bg-red-900/20 dark:border-red-700/30 dark:text-red-300'
        }`}>
          <CheckCircle className="w-3.5 h-3.5 shrink-0" />
          <span>{syncMsg.text}</span>
          <button onClick={() => setSyncMsg(null)} className="ml-auto opacity-60 hover:opacity-100">×</button>
        </div>
      )}

      {/* ── KPI Cards ─────────────────────────────────────────── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-6 gap-4">
        <StatisticCard
          title="Total Emails Scanned"
          value={s.total_emails_scanned ?? 0}
          subtitle="All-time emails processed"
          icon={Mail}
          iconColor="brand"
          loading={statsLoading}
        />
        <StatisticCard
          title="Spam Detected"
          value={s.spam_detected ?? 0}
          subtitle="Flagged by ML models"
          icon={ShieldAlert}
          iconColor="red"
          loading={statsLoading}
        />
        <StatisticCard
          title="Safe Emails"
          value={s.safe_emails ?? 0}
          subtitle="Verified non-spam"
          icon={ShieldCheck}
          iconColor="emerald"
          loading={statsLoading}
        />
        <StatisticCard
          title="Review Required"
          value={(s.review_required ?? 0) + (s.pending_review ?? 0)}
          subtitle="Models disagree / unclassified"
          icon={Clock}
          iconColor="amber"
          loading={statsLoading}
        />
        <StatisticCard
          title="Gmail Status"
          value={auth?.connected ? '🟢 Connected' : '⚫ Not Linked'}
          subtitle={auth?.user?.email || auth?.connected_user?.email || 'No account linked'}
          icon={Wifi}
          iconColor={auth?.connected ? 'emerald' : 'slate'}
          loading={authLoading}
        />
        <StatisticCard
          title="Last Sync"
          value={s.last_sync ? 'Synced' : 'Never'}
          subtitle={s.last_sync?.started_at
            ? new Date(s.last_sync.started_at).toLocaleDateString()
            : 'Connect Gmail to sync'}
          icon={RefreshCw}
          iconColor="purple"
          loading={statsLoading}
        />
      </div>

      {/* ── Main grid ─────────────────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Charts + Recent Emails */}
        <div className="lg:col-span-2 space-y-6">
          {/* Charts row */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <ChartCard
              title="Spam vs Safe (7 days)"
              description="Distribution of email classifications"
              empty
              emptyIcon={BarChart3}
              emptyText="No data yet. Connect Gmail and sync emails to see the chart."
            />
            <ChartCard
              title="Detection Confidence"
              description="Average model confidence over time"
              empty
              emptyIcon={BarChart3}
              emptyText="ML confidence data will appear after emails are processed."
            />
          </div>

          {/* Recent emails */}
          <div className="card">
            <div className="flex items-center justify-between px-5 py-4 border-b border-slate-100 dark:border-navy-700/60">
              <div>
                <h2 className="font-semibold text-slate-800 dark:text-slate-200 text-sm">Recent Emails</h2>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">Latest emails from your inbox</p>
              </div>
              <button
                onClick={() => { refetchEmails(); refetchStats() }}
                className="btn-ghost p-2"
                title="Refresh"
              >
                <RefreshCw className={`w-4 h-4 ${emailsLoading ? 'animate-spin' : ''}`} />
              </button>
            </div>
            <div className="p-2">
              <EmailTable
                emails={emails.slice(0, 8)}
                loading={emailsLoading}
                emptyTitle="No emails synced yet"
                emptyDescription="Connect your Gmail account and sync to see emails here."
              />
            </div>
          </div>
        </div>

        {/* Right: Sidebar widgets */}
        <div className="space-y-5">
          {/* Gmail connect / status card */}
          <GmailConnectCard
            authStatus={auth || { connected: false }}
            onSync={handleSync}
            onDisconnect={handleDisconnect}
          />

          {/* Recent spam activity */}
          <div className="card p-5">
            <div className="flex items-center gap-2 mb-4">
              <AlertTriangle className="w-4 h-4 text-red-500" />
              <h3 className="font-semibold text-slate-800 dark:text-slate-200 text-sm">Recent Spam Activity</h3>
            </div>
            {recentLoading ? (
              <div className="space-y-2">
                {[1,2,3].map(i => (
                  <div key={i} className="h-10 rounded-lg bg-slate-100 dark:bg-navy-700 animate-pulse" />
                ))}
              </div>
            ) : (
              <div className="space-y-2">
                {(recent || []).filter(r => r.label === 'spam').slice(0, 5).length === 0 ? (
                  <p className="text-xs text-slate-500 dark:text-slate-400 text-center py-4">
                    No spam detected yet
                  </p>
                ) : (
                  (recent || []).filter(r => r.label === 'spam').slice(0, 5).map((item, i) => (
                    <div key={i} className="flex items-center gap-2 py-1.5 px-2 rounded-lg hover:bg-slate-50 dark:hover:bg-navy-700/40">
                      <AlertTriangle className="w-3.5 h-3.5 text-red-400 shrink-0" />
                      <div className="min-w-0 flex-1">
                        <p className="text-xs font-medium text-slate-700 dark:text-slate-300 truncate">{item.subject || '(no subject)'}</p>
                        <p className="text-[10px] text-slate-500 truncate">{item.sender}</p>
                      </div>
                      <span className="text-[10px] font-mono text-red-500 shrink-0">
                        {(item.confidence * 100).toFixed(0)}%
                      </span>
                    </div>
                  ))
                )}
              </div>
            )}
          </div>

          {/* Model status */}
          <div className="card p-5">
            <div className="flex items-center gap-2 mb-4">
              <Brain className="w-4 h-4 text-brand-500" />
              <h3 className="font-semibold text-slate-800 dark:text-slate-200 text-sm">ML Model Status</h3>
            </div>
            <div className="space-y-3">
              <ModelStatusRow
                name="Logistic Regression"
                status={s.model_status?.logistic_regression || 'not_trained'}
              />
              <ModelStatusRow
                name="Multinomial Naive Bayes"
                status={s.model_status?.naive_bayes || 'not_trained'}
              />
            </div>
            <div className="mt-4 pt-3 border-t border-slate-100 dark:border-navy-700/60 flex items-center justify-between">
              <span className="text-[11px] text-emerald-600 dark:text-emerald-400 font-medium">
                {s.scheduler_running ? '🟢 Auto-sync active' : 'Active & ready for inference'}
              </span>
              <a
                href="/model-performance"
                className="text-[11px] text-brand-600 dark:text-brand-400 font-semibold hover:underline"
              >
                View Metrics &rarr;
              </a>
            </div>
          </div>

          {/* Quick actions */}
          <div className="card p-5">
            <div className="flex items-center gap-2 mb-4">
              <Zap className="w-4 h-4 text-amber-500" />
              <h3 className="font-semibold text-slate-800 dark:text-slate-200 text-sm">Quick Actions</h3>
            </div>
            <div className="space-y-2">
              {auth?.connected ? (
                <>
                  <QuickAction
                    label="Sync New Emails"
                    description="Incremental check for new messages"
                    icon={RefreshCw}
                    onClick={handleSync}
                    disabled={syncing}
                    loading={syncing}
                  />
                  <QuickAction
                    label="Full Inbox Sync"
                    description="Fetch up to 200 messages from Gmail"
                    icon={Download}
                    onClick={handleFullSync}
                    disabled={syncing}
                    loading={syncing}
                  />
                </>
              ) : (
                <QuickAction
                  label="Connect Gmail"
                  description="Link your Google account"
                  icon={Wifi}
                  onClick={handleConnect}
                  disabled={connecting}
                  loading={connecting}
                />
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function ModelStatusRow({ name, status }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-xs text-slate-600 dark:text-slate-400">{name}</span>
      <StatusBadge status={status} />
    </div>
  )
}

function QuickAction({ label, description, icon: Icon, disabled, onClick, loading }) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className="w-full flex items-center gap-3 p-2.5 rounded-xl text-left hover:bg-slate-50 dark:hover:bg-navy-700/40 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
    >
      <div className="w-8 h-8 rounded-lg bg-slate-100 dark:bg-navy-700 flex items-center justify-center shrink-0">
        <Icon className={`w-4 h-4 text-slate-500 dark:text-slate-400 ${loading ? 'animate-spin' : ''}`} />
      </div>
      <div className="min-w-0">
        <p className="text-xs font-medium text-slate-800 dark:text-slate-200">{label}</p>
        <p className="text-[10px] text-slate-500 dark:text-slate-400">{description}</p>
      </div>
    </button>
  )
}
