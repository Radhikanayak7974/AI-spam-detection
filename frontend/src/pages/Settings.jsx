import { useState, useEffect } from 'react'
import {
  Settings as SettingsIcon, Server, Shield, Bell,
  Database, Key, Save, ExternalLink, AlertTriangle, RefreshCw
} from 'lucide-react'
import useApi from '../hooks/useApi'
import { settingsAPI } from '../services/api'

const SECTIONS = ['General', 'Sync & Scheduler', 'Backend', 'Gmail OAuth', 'ML Models', 'Notifications', 'Danger Zone']

export default function Settings() {
  const [active, setActive] = useState('General')
  const [saved, setSaved] = useState(false)

  function handleSave() {
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
      {/* Sidebar */}
      <div className="card p-3 h-fit lg:sticky lg:top-20">
        <p className="text-[10px] font-semibold text-slate-400 uppercase px-2 py-1 mb-1">Settings</p>
        <nav className="space-y-0.5">
          {SECTIONS.map(s => (
            <button
              key={s}
              onClick={() => setActive(s)}
              className={`w-full text-left px-3 py-2 rounded-xl text-sm font-medium transition-colors ${
                active === s
                  ? 'bg-brand-50 dark:bg-brand-900/20 text-brand-700 dark:text-brand-400'
                  : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-navy-700/60 hover:text-slate-900 dark:hover:text-slate-100'
              }`}
            >
              {s}
            </button>
          ))}
        </nav>
      </div>

      {/* Content */}
      <div className="lg:col-span-3 space-y-5">
        {active === 'General' && <GeneralSettings onSave={handleSave} saved={saved} />}
        {active === 'Sync & Scheduler' && <SyncSettings />}
        {active === 'Backend' && <BackendSettings />}
        {active === 'Gmail OAuth' && <GmailOAuthSettings />}
        {active === 'ML Models' && <MLModelSettings />}
        {active === 'Notifications' && <NotificationSettings />}
        {active === 'Danger Zone' && <DangerZoneSettings />}
      </div>
    </div>
  )
}

function SectionCard({ icon: Icon, title, description, children }) {
  return (
    <div className="card p-5 space-y-4">
      <div className="flex items-center gap-3 pb-3 border-b border-slate-100 dark:border-navy-700/60">
        <div className="w-8 h-8 rounded-lg bg-brand-50 dark:bg-brand-900/20 flex items-center justify-center">
          <Icon className="w-4 h-4 text-brand-600 dark:text-brand-400" />
        </div>
        <div>
          <h3 className="font-semibold text-slate-800 dark:text-slate-200 text-sm">{title}</h3>
          {description && <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">{description}</p>}
        </div>
      </div>
      {children}
    </div>
  )
}

function SettingRow({ label, description, children }) {
  return (
    <div className="flex items-start justify-between gap-4">
      <div>
        <p className="text-sm font-medium text-slate-700 dark:text-slate-300">{label}</p>
        {description && <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">{description}</p>}
      </div>
      <div className="shrink-0">{children}</div>
    </div>
  )
}

function Toggle({ enabled, onChange }) {
  return (
    <button
      onClick={() => onChange(!enabled)}
      className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${
        enabled ? 'bg-brand-600' : 'bg-slate-200 dark:bg-navy-600'
      }`}
    >
      <span className={`inline-block h-4 w-4 rounded-full bg-white shadow transition-transform ${
        enabled ? 'translate-x-4' : 'translate-x-0.5'
      }`} />
    </button>
  )
}

function GeneralSettings({ onSave, saved }) {
  const [darkDefault, setDarkDefault] = useState(false)
  const [autoRefresh, setAutoRefresh]  = useState(true)

  return (
    <SectionCard icon={SettingsIcon} title="General" description="Basic application preferences">
      <SettingRow label="Default Dark Mode" description="Always open in dark mode">
        <Toggle enabled={darkDefault} onChange={setDarkDefault} />
      </SettingRow>
      <SettingRow label="Auto-refresh Dashboard" description="Refresh stats every 60 seconds">
        <Toggle enabled={autoRefresh} onChange={setAutoRefresh} />
      </SettingRow>
      <SettingRow label="App Version" description="Current phase">
        <span className="badge bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400 text-xs">Phase 4: Advanced Analytics, Feedback Loop &amp; Retraining</span>
      </SettingRow>
      <button onClick={onSave} className="btn-primary text-xs gap-1.5 mt-2">
        <Save className="w-3.5 h-3.5" />
        {saved ? 'Saved!' : 'Save Changes'}
      </button>
    </SectionCard>
  )
}

function SyncSettings() {
  const { data: syncConfig, loading, refetch } = useApi(settingsAPI.getSyncSettings)
  const [autoSync, setAutoSync] = useState(true)
  const [interval, setIntervalVal] = useState(5)
  const [saving, setSaving] = useState(false)
  const [saveMsg, setSaveMsg] = useState(null)

  useEffect(() => {
    if (syncConfig) {
      if (syncConfig.auto_sync_enabled !== undefined) {
        setAutoSync(Boolean(syncConfig.auto_sync_enabled))
      }
      if (syncConfig.sync_interval_minutes !== undefined) {
        setIntervalVal(Number(syncConfig.sync_interval_minutes))
      }
    }
  }, [syncConfig])

  async function handleSaveSync() {
    setSaving(true)
    setSaveMsg(null)
    try {
      await settingsAPI.updateSyncSettings({
        auto_sync_enabled: autoSync,
        sync_interval_minutes: interval,
      })
      setSaveMsg('Sync preferences saved successfully!')
      refetch()
    } catch (err) {
      setSaveMsg(err.userMessage || 'Failed to save sync preferences')
    } finally {
      setSaving(false)
      setTimeout(() => setSaveMsg(null), 3000)
    }
  }

  const nextRun = syncConfig?.scheduler_info?.next_run
  const isSchedulerOn = syncConfig?.scheduler_running

  return (
    <SectionCard
      icon={RefreshCw}
      title="Gmail Synchronization & Background Scheduler"
      description="Configure automatic background sync intervals and ML classification frequency"
    >
      {loading ? (
        <p className="text-xs text-slate-500 py-3">Loading sync preferences...</p>
      ) : (
        <>
          <div className="rounded-xl bg-slate-50 dark:bg-navy-700/40 p-4 border border-slate-100 dark:border-navy-700/60 flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold text-slate-800 dark:text-slate-200">
                Background Scheduler Status
              </p>
              <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">
                {isSchedulerOn
                  ? `Active • Running job every ${interval} minute(s)`
                  : 'Inactive / Paused'}
                {nextRun && ` • Next sync at: ${new Date(nextRun).toLocaleTimeString()}`}
              </p>
            </div>
            <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
              isSchedulerOn
                ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400'
                : 'bg-slate-200 text-slate-600 dark:bg-navy-600 dark:text-slate-400'
            }`}>
              {isSchedulerOn ? '● Active' : '○ Disabled'}
            </span>
          </div>

          <SettingRow
            label="Automatic Background Sync"
            description="Periodically fetch and scan new Gmail messages automatically"
          >
            <Toggle enabled={autoSync} onChange={setAutoSync} />
          </SettingRow>

          <SettingRow
            label="Sync Interval"
            description="How frequently to check for new messages"
          >
            <select
              value={interval}
              onChange={(e) => setIntervalVal(Number(e.target.value))}
              disabled={!autoSync}
              className="text-xs bg-white dark:bg-navy-800 border border-slate-200 dark:border-navy-600 rounded-lg px-2.5 py-1.5 text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-1 focus:ring-brand-500 disabled:opacity-50"
            >
              <option value={1}>Every 1 minute</option>
              <option value={5}>Every 5 minutes (Recommended)</option>
              <option value={10}>Every 10 minutes</option>
              <option value={15}>Every 15 minutes</option>
              <option value={30}>Every 30 minutes</option>
              <option value={60}>Every 1 hour</option>
            </select>
          </SettingRow>

          <div className="pt-2 flex items-center gap-3">
            <button
              onClick={handleSaveSync}
              disabled={saving}
              className="btn-primary text-xs gap-1.5"
            >
              <Save className="w-3.5 h-3.5" />
              {saving ? 'Saving...' : 'Save Sync Settings'}
            </button>
            {saveMsg && (
              <span className="text-xs text-brand-600 dark:text-brand-400 font-medium animate-fade-in">
                {saveMsg}
              </span>
            )}
          </div>
        </>
      )}
    </SectionCard>
  )
}

function BackendSettings() {
  return (
    <SectionCard icon={Server} title="Backend API" description="Flask server configuration">
      <SettingRow label="API Base URL" description="The Flask backend endpoint">
        <code className="text-xs bg-slate-100 dark:bg-navy-700 px-2 py-1 rounded-lg font-mono text-slate-700 dark:text-slate-300">
          http://localhost:5000/api
        </code>
      </SettingRow>
      <SettingRow label="Database" description="SQLite storage location">
        <code className="text-xs bg-slate-100 dark:bg-navy-700 px-2 py-1 rounded-lg font-mono text-slate-700 dark:text-slate-300">
          backend/spam_detection.db
        </code>
      </SettingRow>
      <SettingRow label="Environment" description="Current Flask environment">
        <span className="badge bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400 text-xs">development</span>
      </SettingRow>
    </SectionCard>
  )
}

function GmailOAuthSettings() {
  return (
    <SectionCard icon={Key} title="Gmail OAuth 2.0" description="Google API credentials & authorization">
      <div className="rounded-xl bg-blue-50 dark:bg-blue-900/10 border border-blue-200 dark:border-blue-800/30 p-3 flex gap-2">
        <Key className="w-4 h-4 text-blue-600 dark:text-blue-400 shrink-0 mt-0.5" />
        <div>
          <p className="text-xs font-semibold text-blue-800 dark:text-blue-300">OAuth 2.0 Endpoints Ready</p>
          <p className="text-xs text-blue-600 dark:text-blue-400 mt-0.5">
            Add your Google Cloud client credentials to <code className="font-mono bg-blue-100 dark:bg-blue-900/40 px-1 rounded">.env</code> to enable live Gmail sync.
          </p>
        </div>
      </div>
      <SettingRow label="Redirect URI" description="Register this in Google Cloud Console">
        <code className="text-xs bg-slate-100 dark:bg-navy-700 px-2 py-1 rounded-lg font-mono text-brand-600 dark:text-brand-400">
          http://localhost:5000/api/auth/callback
        </code>
      </SettingRow>
      <SettingRow label="Permissions" description="OAuth scopes requested">
        <span className="text-xs text-slate-600 dark:text-slate-400 font-mono">
          gmail.readonly, gmail.modify, userinfo
        </span>
      </SettingRow>
      <a
        href="https://console.cloud.google.com/apis/credentials"
        target="_blank"
        rel="noopener noreferrer"
        className="btn-secondary text-xs gap-1.5 self-start"
      >
        <ExternalLink className="w-3 h-3" />
        Google Cloud Console
      </a>
    </SectionCard>
  )
}


function MLModelSettings() {
  return (
    <SectionCard icon={Database} title="ML Models" description="Machine learning configuration">
      <div className="space-y-2">
        {[
          { name: 'Logistic Regression', param: 'C=1.0, max_iter=1000, solver=lbfgs' },
          { name: 'Multinomial Naive Bayes', param: 'alpha=1.0 (Laplace smoothing)' },
        ].map(m => (
          <div key={m.name} className="p-3 rounded-xl bg-slate-50 dark:bg-navy-700/40">
            <p className="text-xs font-semibold text-slate-700 dark:text-slate-300">{m.name}</p>
            <p className="text-[10px] font-mono text-slate-500 dark:text-slate-400 mt-1">{m.param}</p>
          </div>
        ))}
      </div>
      <SettingRow label="Model Directory" description="Where trained models are saved">
        <code className="text-xs bg-slate-100 dark:bg-navy-700 px-2 py-1 rounded-lg font-mono text-slate-600 dark:text-slate-400">
          ml_models/
        </code>
      </SettingRow>
    </SectionCard>
  )
}

function NotificationSettings() {
  const [emailAlerts, setEmailAlerts] = useState(false)
  const [spamAlerts,  setSpamAlerts]  = useState(true)

  return (
    <SectionCard icon={Bell} title="Notifications" description="Alert preferences">
      <SettingRow label="Email Alerts" description="Get notified about new spam via email">
        <Toggle enabled={emailAlerts} onChange={setEmailAlerts} />
      </SettingRow>
      <SettingRow label="In-app Spam Alerts" description="Show alerts when spam is detected">
        <Toggle enabled={spamAlerts} onChange={setSpamAlerts} />
      </SettingRow>
      <p className="text-xs text-slate-400 dark:text-slate-500">
        Notification delivery will be implemented in a future phase.
      </p>
    </SectionCard>
  )
}

function DangerZoneSettings() {
  return (
    <div className="card p-5 border-red-200 dark:border-red-900/50 space-y-4">
      <div className="flex items-center gap-2 pb-3 border-b border-red-100 dark:border-red-900/40">
        <AlertTriangle className="w-4 h-4 text-red-500" />
        <h3 className="font-semibold text-red-600 dark:text-red-400 text-sm">Danger Zone</h3>
      </div>
      <SettingRow
        label="Clear All Emails"
        description="Permanently delete all synced emails from the database"
      >
        <button disabled className="btn-danger text-xs opacity-50 cursor-not-allowed">Delete All</button>
      </SettingRow>
      <SettingRow
        label="Reset ML Models"
        description="Delete trained model files and reset to untrained state"
      >
        <button disabled className="btn-danger text-xs opacity-50 cursor-not-allowed">Reset Models</button>
      </SettingRow>
      <p className="text-xs text-slate-400 dark:text-slate-500">
        Destructive actions are disabled in Phase 1.
      </p>
    </div>
  )
}
