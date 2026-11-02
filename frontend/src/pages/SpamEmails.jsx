import { ShieldAlert, RefreshCw } from 'lucide-react'
import EmailTable from '../components/EmailTable'
import useApi from '../hooks/useApi'
import { emailsAPI } from '../services/api'

export default function SpamEmails() {
  const { data, loading, refetch } = useApi(emailsAPI.spam)
  const emails = data?.items || data || []

  return (
    <div className="space-y-4">
      <div className="card">
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-100 dark:border-navy-700/60">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-red-50 dark:bg-red-900/20 flex items-center justify-center">
              <ShieldAlert className="w-4 h-4 text-red-500" />
            </div>
            <div>
              <h2 className="font-semibold text-slate-800 dark:text-slate-200 text-sm">Spam Emails</h2>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                {data?.meta?.total ?? 0} spam emails detected
              </p>
            </div>
          </div>
          <button onClick={refetch} className="btn-secondary text-xs gap-1.5">
            <RefreshCw className="w-3.5 h-3.5" />
            Refresh
          </button>
        </div>

        {/* Summary bar */}
        {!loading && emails.length === 0 && (
          <div className="px-5 py-3 bg-emerald-50 dark:bg-emerald-900/10 border-b border-emerald-100 dark:border-emerald-900/30">
            <p className="text-xs text-emerald-700 dark:text-emerald-400 font-medium">
              ✅ No spam detected. Your inbox is clean!
            </p>
          </div>
        )}

        <div className="p-2">
          <EmailTable
            emails={emails}
            loading={loading}
            emptyTitle="No spam detected yet"
            emptyDescription="Connect Gmail and scan your emails. Spam emails will appear here."
          />
        </div>
      </div>
    </div>
  )
}
