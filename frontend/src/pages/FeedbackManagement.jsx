import { useState, useEffect, useCallback } from 'react'
import {
  MessageSquare, CheckCircle2, AlertTriangle, Search,
  Filter, Trash2, Check, X, ShieldAlert, ShieldCheck, RefreshCw,
  Sparkles, Clock, Calendar, ArrowRight
} from 'lucide-react'
import { feedbackAPI } from '../services/api'
import StatusBadge from '../components/StatusBadge'
import LoadingSpinner from '../components/LoadingSpinner'
import EmptyState from '../components/EmptyState'

function formatDate(iso) {
  if (!iso) return '—'
  const d = new Date(iso)
  return d.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export default function FeedbackManagement() {
  const [stats, setStats] = useState(null)
  const [feedbackItems, setFeedbackItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [loadingStats, setLoadingStats] = useState(true)

  // Filters & pagination
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [labelFilter, setLabelFilter] = useState('all')
  const [correctionOnly, setCorrectionOnly] = useState(false)
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [totalCount, setTotalCount] = useState(0)

  // Fetch stats
  const fetchStats = async () => {
    try {
      setLoadingStats(true)
      const res = await feedbackAPI.stats()
      setStats(res.data?.data || null)
    } catch (err) {
      console.error('Failed to load feedback stats:', err)
    } finally {
      setLoadingStats(false)
    }
  };

  // Fetch feedback records
  const fetchFeedback = useCallback(async () => {
    try {
      setLoading(true)
      const res = await feedbackAPI.list({
        page,
        per_page: 15,
        search: search.trim() || undefined,
        status: statusFilter !== 'all' ? statusFilter : undefined,
        label: labelFilter !== 'all' ? labelFilter : undefined,
        correction_only: correctionOnly ? 'true' : undefined,
      })
      const data = res.data
      setFeedbackItems(data?.data || [])
      setTotalPages(data?.meta?.pages || 1)
      setTotalCount(data?.meta?.total || 0)
    } catch (err) {
      console.error('Failed to load feedback list:', err)
    } finally {
      setLoading(false)
    }
  }, [page, search, statusFilter, labelFilter, correctionOnly])

  useEffect(() => {
    fetchStats()
  }, [])

  useEffect(() => {
    fetchFeedback()
  }, [fetchFeedback])

  // Handle status update
  const handleUpdateStatus = async (id, newStatus) => {
    try {
      await feedbackAPI.update(id, { status: newStatus })
      fetchFeedback()
      fetchStats()
    } catch (err) {
      alert(err?.userMessage || 'Failed to update feedback status')
    }
  }

  // Handle delete
  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this feedback record?')) return
    try {
      await feedbackAPI.delete(id)
      fetchFeedback()
      fetchStats()
    } catch (err) {
      alert(err?.userMessage || 'Failed to delete feedback record')
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="card p-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-purple-50 dark:bg-purple-900/20 flex items-center justify-center">
              <MessageSquare className="w-5 h-5 text-purple-600 dark:text-purple-400" />
            </div>
            <div>
              <h2 className="font-semibold text-slate-800 dark:text-slate-200">
                User Feedback Loop & Retraining Curation
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                Audit user corrections, manage feedback labels, and curate training samples for model retraining.
              </p>
            </div>
          </div>
          <button
            onClick={() => {
              fetchStats()
              fetchFeedback()
            }}
            className="btn-secondary text-xs flex items-center gap-1.5 self-start sm:self-auto"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Refresh
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Feedback */}
        <div className="card p-4">
          <p className="text-xs text-slate-500 dark:text-slate-400 font-medium">Total Feedback</p>
          <p className="text-2xl font-bold text-slate-900 dark:text-white mt-1">
            {loadingStats ? '—' : stats?.total_feedback || 0}
          </p>
          <p className="text-[11px] text-slate-400 mt-0.5">Submitted by users</p>
        </div>

        {/* User Corrections */}
        <div className="card p-4">
          <p className="text-xs text-slate-500 dark:text-slate-400 font-medium">Disagreements / Corrections</p>
          <div className="flex items-baseline gap-2 mt-1">
            <p className="text-2xl font-bold text-amber-600 dark:text-amber-400">
              {loadingStats ? '—' : stats?.corrections_count || 0}
            </p>
            <span className="text-xs text-slate-400">
              ({stats?.total_feedback ? `${(stats.disagreement_rate * 100).toFixed(1)}%` : '0%'})
            </span>
          </div>
          <p className="text-[11px] text-slate-400 mt-0.5">Model predictions corrected</p>
        </div>

        {/* Approved for Retraining */}
        <div className="card p-4">
          <p className="text-xs text-slate-500 dark:text-slate-400 font-medium">Approved for Training</p>
          <p className="text-2xl font-bold text-emerald-600 dark:text-emerald-400 mt-1">
            {loadingStats ? '—' : stats?.approved_count || 0}
          </p>
          <p className="text-[11px] text-slate-400 mt-0.5">Active in retraining pool</p>
        </div>

        {/* Agreement Rate */}
        <div className="card p-4">
          <p className="text-xs text-slate-500 dark:text-slate-400 font-medium">User Agreement Rate</p>
          <p className="text-2xl font-bold text-brand-600 dark:text-brand-400 mt-1">
            {loadingStats ? '—' : `${((stats?.agreement_rate || 1.0) * 100).toFixed(1)}%`}
          </p>
          <p className="text-[11px] text-slate-400 mt-0.5">Perceived model accuracy</p>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="card p-4 space-y-3">
        <div className="flex flex-col sm:flex-row gap-3 items-stretch sm:items-center justify-between">
          {/* Search bar */}
          <div className="relative flex-1 max-w-md">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={search}
              onChange={(e) => {
                setSearch(e.target.value)
                setPage(1)
              }}
              placeholder="Search by subject, sender, or notes..."
              className="input pl-9 text-xs w-full py-2"
            />
          </div>

          {/* Filters */}
          <div className="flex flex-wrap items-center gap-2">
            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value)
                setPage(1)
              }}
              className="input text-xs py-2 px-3"
            >
              <option value="all">All Statuses</option>
              <option value="approved">Approved</option>
              <option value="pending">Pending</option>
              <option value="rejected">Rejected</option>
            </select>

            <select
              value={labelFilter}
              onChange={(e) => {
                setLabelFilter(e.target.value)
                setPage(1)
              }}
              className="input text-xs py-2 px-3"
            >
              <option value="all">All Labels</option>
              <option value="spam">Spam Only</option>
              <option value="ham">Safe Only</option>
            </select>

            <button
              onClick={() => {
                setCorrectionOnly(!correctionOnly)
                setPage(1)
              }}
              className={`btn text-xs px-3 py-2 rounded-lg border transition-all ${
                correctionOnly
                  ? 'bg-amber-100 text-amber-800 border-amber-300 dark:bg-amber-950/40 dark:text-amber-300 dark:border-amber-700'
                  : 'btn-secondary'
              }`}
            >
              {correctionOnly ? '✓ Corrections Only' : 'Corrections Only'}
            </button>
          </div>
        </div>
      </div>

      {/* Feedback Table */}
      <div className="card overflow-hidden">
        {loading ? (
          <div className="p-12 flex justify-center">
            <LoadingSpinner size="md" message="Loading feedback records..." />
          </div>
        ) : feedbackItems.length === 0 ? (
          <div className="p-8">
            <EmptyState
              icon={MessageSquare}
              title="No feedback records found"
              description="When users flag emails as spam or safe in the inbox, their corrections and confirmations will appear here."
            />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Email Subject & Sender</th>
                  <th>Model Prediction</th>
                  <th>User Corrected Label</th>
                  <th>Correction?</th>
                  <th>Notes</th>
                  <th>Submitted</th>
                  <th>Retraining Status</th>
                  <th className="text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {feedbackItems.map((fb) => (
                  <tr key={fb.id} className="hover:bg-slate-50/70 dark:hover:bg-navy-700/40 transition-colors">
                    <td>
                      <div className="min-w-0 max-w-[280px]">
                        <p className="font-semibold text-slate-800 dark:text-slate-200 text-xs truncate">
                          {fb.email?.subject || '(no subject)'}
                        </p>
                        <p className="text-[11px] text-slate-500 dark:text-slate-400 truncate mt-0.5">
                          {fb.email?.sender_email || fb.email?.sender || '—'}
                        </p>
                      </div>
                    </td>

                    <td>
                      <StatusBadge status={fb.model_label || 'unknown'} />
                    </td>

                    <td>
                      <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                        fb.user_label === 'spam'
                          ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
                          : 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400'
                      }`}>
                        {fb.user_label === 'spam' ? (
                          <ShieldAlert className="w-3 h-3 shrink-0" />
                        ) : (
                          <ShieldCheck className="w-3 h-3 shrink-0" />
                        )}
                        {fb.user_label.toUpperCase()}
                      </span>
                    </td>

                    <td>
                      {fb.is_correction ? (
                        <span className="text-[11px] font-semibold text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-950/30 px-2 py-0.5 rounded-md border border-amber-200 dark:border-amber-800/40">
                          Overridden
                        </span>
                      ) : (
                        <span className="text-[11px] text-slate-500 dark:text-slate-400">
                          Confirmed
                        </span>
                      )}
                    </td>

                    <td>
                      <span className="text-xs text-slate-600 dark:text-slate-300 max-w-[180px] truncate block">
                        {fb.notes || '—'}
                      </span>
                    </td>

                    <td>
                      <span className="text-[11px] text-slate-500 dark:text-slate-400 whitespace-nowrap">
                        {formatDate(fb.created_at)}
                      </span>
                    </td>

                    <td>
                      <span className={`text-[11px] font-semibold px-2 py-0.5 rounded-full capitalize ${
                        fb.status === 'approved'
                          ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-300'
                          : fb.status === 'rejected'
                          ? 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300'
                          : 'bg-slate-100 text-slate-700 dark:bg-navy-700 dark:text-slate-300'
                      }`}>
                        {fb.status}
                      </span>
                    </td>

                    <td className="text-right">
                      <div className="flex items-center justify-end gap-1">
                        {fb.status !== 'approved' && (
                          <button
                            onClick={() => handleUpdateStatus(fb.id, 'approved')}
                            title="Approve for retraining"
                            className="p-1 rounded text-emerald-600 hover:bg-emerald-50 dark:hover:bg-emerald-950/30"
                          >
                            <Check className="w-4 h-4" />
                          </button>
                        )}
                        {fb.status !== 'rejected' && (
                          <button
                            onClick={() => handleUpdateStatus(fb.id, 'rejected')}
                            title="Reject from retraining"
                            className="p-1 rounded text-amber-600 hover:bg-amber-50 dark:hover:bg-amber-950/30"
                          >
                            <X className="w-4 h-4" />
                          </button>
                        )}
                        <button
                          onClick={() => handleDelete(fb.id)}
                          title="Delete record"
                          className="p-1 rounded text-red-500 hover:bg-red-50 dark:hover:bg-red-950/30"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination footer */}
        {totalPages > 1 && (
          <div className="p-4 border-t border-slate-100 dark:border-navy-700 flex items-center justify-between text-xs text-slate-500">
            <span>
              Showing {(page - 1) * 15 + 1}–{Math.min(page * 15, totalCount)} of {totalCount} records
            </span>
            <div className="flex gap-1.5">
              <button
                disabled={page <= 1}
                onClick={() => setPage((p) => p - 1)}
                className="btn-secondary text-xs px-2.5 py-1"
              >
                Previous
              </button>
              <button
                disabled={page >= totalPages}
                onClick={() => setPage((p) => p + 1)}
                className="btn-secondary text-xs px-2.5 py-1"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
