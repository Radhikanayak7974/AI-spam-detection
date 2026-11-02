import { useState } from 'react'
import {
  Mail, AlertTriangle, ChevronRight, X, Brain, CheckCircle,
  HelpCircle, Sparkles, Calendar, User, ThumbsUp, ThumbsDown,
  MessageSquare, ShieldCheck, ShieldAlert, Check
} from 'lucide-react'
import StatusBadge from './StatusBadge'
import EmptyState from './EmptyState'
import LoadingSpinner from './LoadingSpinner'
import { feedbackAPI } from '../services/api'

function formatDate(iso) {
  if (!iso) return '—'
  const d = new Date(iso)
  return d.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

/**
 * EmailTable – displays paginated email rows with interactive ML detail modal.
 */
export default function EmailTable({
  emails = [],
  loading = false,
  onRowClick,
  emptyTitle = 'No emails yet',
  emptyDescription = 'Emails will appear here after Gmail is connected and synced.',
}) {
  const [selectedEmail, setSelectedEmail] = useState(null)

  if (loading) {
    return (
      <div className="flex items-center justify-center py-16">
        <LoadingSpinner size="md" />
      </div>
    )
  }

  if (!emails.length) {
    return (
      <EmptyState
        icon={Mail}
        title={emptyTitle}
        description={emptyDescription}
      />
    )
  }

  function handleRowSelect(email) {
    if (onRowClick) {
      onRowClick(email)
    } else {
      setSelectedEmail(email)
    }
  }

  return (
    <>
      <div className="overflow-x-auto rounded-xl">
        <table className="data-table">
          <thead>
            <tr>
              <th>Subject</th>
              <th>Sender</th>
              <th>Status</th>
              <th>Confidence</th>
              <th>Received</th>
              <th className="w-8"></th>
            </tr>
          </thead>
          <tbody>
            {emails.map((email) => (
              <tr
                key={email.id}
                onClick={() => handleRowSelect(email)}
                className="cursor-pointer hover:bg-slate-50 dark:hover:bg-navy-700/50 transition-colors"
              >
                <td>
                  <div className="flex items-center gap-2 min-w-0">
                    {email.prediction?.label === 'spam' && (
                      <AlertTriangle className="w-3.5 h-3.5 text-red-500 shrink-0" />
                    )}
                    <span className="truncate max-w-[280px] font-medium text-slate-800 dark:text-slate-200">
                      {email.subject || '(no subject)'}
                    </span>
                  </div>
                </td>
                <td>
                  <span className="text-slate-600 dark:text-slate-400 truncate max-w-[180px] block text-xs">
                    {email.sender_email || email.sender || '—'}
                  </span>
                </td>
                <td>
                  {email.prediction ? (
                    <StatusBadge status={email.prediction.label} />
                  ) : (
                    <StatusBadge status="pending" />
                  )}
                </td>
                <td>
                  <span className="text-slate-700 dark:text-slate-300 font-mono text-xs">
                    {email.prediction
                      ? `${(email.prediction.confidence * 100).toFixed(1)}%`
                      : '—'}
                  </span>
                </td>
                <td>
                  <span className="text-xs text-slate-500 dark:text-slate-400">
                    {formatDate(email.received_at)}
                  </span>
                </td>
                <td>
                  <ChevronRight className="w-4 h-4 text-slate-400" />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Email Detail & ML Classification Modal */}
      {selectedEmail && (
        <EmailDetailModal
          email={selectedEmail}
          onClose={() => setSelectedEmail(null)}
        />
      )}
    </>
  )
}

function EmailDetailModal({ email, onClose }) {
  const pred = email.prediction
  const details = pred?.details || {}
  const lr = details.logistic_regression
  const nb = details.naive_bayes
  const signals = details.top_signals || []

  // Feedback state
  const [feedbackLabel, setFeedbackLabel] = useState(null)
  const [feedbackNotes, setFeedbackNotes] = useState('')
  const [submittingFeedback, setSubmittingFeedback] = useState(false)
  const [feedbackSuccess, setFeedbackSuccess] = useState(false)
  const [feedbackMessage, setFeedbackMessage] = useState('')

  const handleFeedbackSubmit = async (chosenLabel) => {
    const labelToSend = chosenLabel || feedbackLabel
    if (!labelToSend) return

    try {
      setSubmittingFeedback(true)
      const res = await feedbackAPI.submit({
        email_id: email.id,
        user_label: labelToSend,
        notes: feedbackNotes.trim(),
        status: 'approved',
      })
      setFeedbackSuccess(true)
      setFeedbackMessage(
        res.data?.data?.is_correction
          ? 'Prediction correction recorded! This sample is queued for controlled retraining.'
          : 'Classification confirmed! Feedback recorded for retraining audit.'
      )
    } catch (err) {
      alert(err?.userMessage || 'Failed to submit feedback')
    } finally {
      setSubmittingFeedback(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fade-in">
      <div className="card w-full max-w-2xl max-h-[90vh] flex flex-col shadow-2xl relative border border-slate-200 dark:border-navy-700 overflow-hidden">
        {/* Header */}
        <div className="p-5 border-b border-slate-100 dark:border-navy-700/60 flex items-start justify-between gap-4">
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2 mb-1.5">
              {pred ? (
                <StatusBadge status={pred.label} />
              ) : (
                <StatusBadge status="pending" />
              )}
              <span className="text-[11px] text-slate-400 font-mono">
                ID: {email.gmail_message_id || email.id}
              </span>
            </div>
            <h3 className="font-bold text-slate-900 dark:text-slate-100 text-base leading-snug break-words">
              {email.subject || '(no subject)'}
            </h3>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content body */}
        <div className="p-5 overflow-y-auto space-y-5 flex-1">
          {/* Metadata */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs bg-slate-50 dark:bg-navy-800/50 p-3.5 rounded-xl border border-slate-100 dark:border-navy-700/50">
            <div className="flex items-center gap-2 text-slate-600 dark:text-slate-300">
              <User className="w-4 h-4 text-slate-400 shrink-0" />
              <span className="truncate">
                <strong>From:</strong> {email.sender || email.sender_email || '—'}
              </span>
            </div>
            <div className="flex items-center gap-2 text-slate-600 dark:text-slate-300">
              <Calendar className="w-4 h-4 text-slate-400 shrink-0" />
              <span>
                <strong>Date:</strong> {formatDate(email.received_at)}
              </span>
            </div>
          </div>

          {/* ML Models Breakdown (Logistic Regression vs Naive Bayes) */}
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <Brain className="w-4 h-4 text-brand-500" />
              <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-400">
                Machine Learning Dual-Model Analysis
              </h4>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {/* Logistic Regression Card */}
              <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-navy-800/40 border border-slate-100 dark:border-navy-700/60">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                    Logistic Regression
                  </span>
                  {lr ? (
                    <span className={`text-[11px] font-semibold px-2 py-0.5 rounded ${
                      lr.prediction === 'SPAM'
                        ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
                        : 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400'
                    }`}>
                      {lr.prediction}
                    </span>
                  ) : (
                    <span className="text-[11px] text-slate-400">Model evaluated</span>
                  )}
                </div>
                <div className="space-y-1 text-xs text-slate-500 dark:text-slate-400 font-mono">
                  <div className="flex justify-between">
                    <span>Confidence:</span>
                    <span className="text-slate-800 dark:text-slate-200 font-semibold">
                      {lr ? `${(lr.confidence * 100).toFixed(1)}%` : `${((pred?.confidence || 0) * 100).toFixed(1)}%`}
                    </span>
                  </div>
                  {lr?.spam_probability !== undefined && (
                    <div className="flex justify-between">
                      <span>Spam Probability:</span>
                      <span className="text-slate-800 dark:text-slate-200">
                        {(lr.spam_probability * 100).toFixed(1)}%
                      </span>
                    </div>
                  )}
                </div>
              </div>

              {/* Multinomial Naive Bayes Card */}
              <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-navy-800/40 border border-slate-100 dark:border-navy-700/60">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                    Multinomial Naive Bayes
                  </span>
                  {nb ? (
                    <span className={`text-[11px] font-semibold px-2 py-0.5 rounded ${
                      nb.prediction === 'SPAM'
                        ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
                        : 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400'
                    }`}>
                      {nb.prediction}
                    </span>
                  ) : (
                    <span className="text-[11px] text-slate-400">Model evaluated</span>
                  )}
                </div>
                <div className="space-y-1 text-xs text-slate-500 dark:text-slate-400 font-mono">
                  <div className="flex justify-between">
                    <span>Confidence:</span>
                    <span className="text-slate-800 dark:text-slate-200 font-semibold">
                      {nb ? `${(nb.confidence * 100).toFixed(1)}%` : '—'}
                    </span>
                  </div>
                  {nb?.spam_probability !== undefined && (
                    <div className="flex justify-between">
                      <span>Spam Probability:</span>
                      <span className="text-slate-800 dark:text-slate-200">
                        {(nb.spam_probability * 100).toFixed(1)}%
                      </span>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Decision Logic explanation */}
            <div className="p-3 rounded-xl bg-brand-50/50 dark:bg-brand-900/10 border border-brand-100 dark:border-brand-800/20 text-xs text-brand-800 dark:text-brand-300 flex items-start gap-2">
              <Sparkles className="w-4 h-4 shrink-0 mt-0.5" />
              <div>
                <strong>Ensemble Decision: </strong>
                {pred?.label === 'spam' && 'Both models flagged as Spam (or highest confidence spam indicator).'}
                {pred?.label === 'ham' && 'Both models classified message as legitimate / safe.'}
                {pred?.label === 'review' && 'Models disagreed on classification. Marked for human review.'}
                {!pred && 'Pending prediction scan.'}
              </div>
            </div>
          </div>

          {/* User Feedback Loop Section */}
          <div className="p-4 rounded-xl bg-slate-50 dark:bg-navy-800/40 border border-slate-200 dark:border-navy-700 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <MessageSquare className="w-4 h-4 text-purple-600 dark:text-purple-400" />
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
                  User Feedback & Retraining Loop
                </h4>
              </div>
              <span className="text-[11px] text-slate-500 dark:text-slate-400">
                Correct or confirm to retrain ML models
              </span>
            </div>

            {feedbackSuccess ? (
              <div className="p-3 bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-800/40 rounded-lg flex items-center gap-2 text-xs text-emerald-800 dark:text-emerald-300">
                <Check className="w-4 h-4 text-emerald-600 shrink-0" />
                <span>{feedbackMessage}</span>
              </div>
            ) : (
              <div className="space-y-3">
                <div className="flex flex-wrap gap-2">
                  <button
                    type="button"
                    onClick={() => {
                      setFeedbackLabel('spam')
                      handleFeedbackSubmit('spam')
                    }}
                    disabled={submittingFeedback}
                    className={`btn text-xs px-3 py-1.5 flex items-center gap-1.5 rounded-lg border transition-all ${
                      feedbackLabel === 'spam'
                        ? 'bg-red-600 text-white border-red-600'
                        : 'border-red-200 text-red-700 dark:border-red-800/40 dark:text-red-300 hover:bg-red-50 dark:hover:bg-red-950/20'
                    }`}
                  >
                    <ShieldAlert className="w-3.5 h-3.5" />
                    Mark as Spam
                  </button>

                  <button
                    type="button"
                    onClick={() => {
                      setFeedbackLabel('ham')
                      handleFeedbackSubmit('ham')
                    }}
                    disabled={submittingFeedback}
                    className={`btn text-xs px-3 py-1.5 flex items-center gap-1.5 rounded-lg border transition-all ${
                      feedbackLabel === 'ham'
                        ? 'bg-emerald-600 text-white border-emerald-600'
                        : 'border-emerald-200 text-emerald-700 dark:border-emerald-800/40 dark:text-emerald-300 hover:bg-emerald-50 dark:hover:bg-emerald-950/20'
                    }`}
                  >
                    <ShieldCheck className="w-3.5 h-3.5" />
                    Mark as Not Spam (Safe)
                  </button>

                  <button
                    type="button"
                    onClick={() => {
                      const opposite = pred?.label === 'spam' ? 'ham' : 'spam'
                      setFeedbackLabel(opposite)
                      handleFeedbackSubmit(opposite)
                    }}
                    disabled={submittingFeedback}
                    className="btn-secondary text-xs px-3 py-1.5 flex items-center gap-1.5 text-amber-700 dark:text-amber-400"
                  >
                    <AlertTriangle className="w-3.5 h-3.5" />
                    Report Incorrect
                  </button>

                  <button
                    type="button"
                    onClick={() => {
                      const current = pred?.label === 'spam' ? 'spam' : 'ham'
                      setFeedbackLabel(current)
                      handleFeedbackSubmit(current)
                    }}
                    disabled={submittingFeedback}
                    className="btn-secondary text-xs px-3 py-1.5 flex items-center gap-1.5 text-blue-700 dark:text-blue-400"
                  >
                    <CheckCircle className="w-3.5 h-3.5" />
                    Confirm Classification
                  </button>
                </div>

                <div className="flex gap-2">
                  <input
                    type="text"
                    value={feedbackNotes}
                    onChange={(e) => setFeedbackNotes(e.target.value)}
                    placeholder="Optional note / reasoning for correction (e.g. false positive promo email)..."
                    className="input text-xs flex-1 py-1.5 px-3"
                  />
                </div>
              </div>
            )}
          </div>

          {/* Top signals / keywords */}
          {signals.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-400 mb-2">
                Top Signal Keywords
              </h4>
              <div className="flex flex-wrap gap-1.5">
                {signals.map((sig, i) => (
                  <span
                    key={i}
                    className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs bg-slate-100 dark:bg-navy-700 text-slate-700 dark:text-slate-300 font-mono"
                  >
                    <span>{sig.word}</span>
                    <span className={`text-[10px] font-bold ${sig.score > 0 ? 'text-red-500' : 'text-emerald-500'}`}>
                      {sig.score > 0 ? `+${sig.score}` : sig.score}
                    </span>
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Email Snippet / Body */}
          <div>
            <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-400 mb-2">
              Email Content Preview
            </h4>
            <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-navy-900/60 border border-slate-100 dark:border-navy-700/60 text-xs text-slate-700 dark:text-slate-300 whitespace-pre-wrap font-sans max-h-48 overflow-y-auto leading-relaxed">
              {email.body_plain || email.snippet || '(empty message body)'}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-slate-100 dark:border-navy-700/60 flex justify-end">
          <button onClick={onClose} className="btn-secondary text-xs px-4 py-2">
            Close
          </button>
        </div>
      </div>
    </div>
  )
}
