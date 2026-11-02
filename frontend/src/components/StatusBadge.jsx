import clsx from 'clsx'

const variants = {
  spam:        'badge-spam',
  ham:         'badge-safe',
  safe:        'badge-safe',
  pending:     'badge-pending',
  connected:   'badge-connected',
  disconnected:'badge-disconnected',
  running:     'badge bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
  completed:   'badge-safe',
  failed:      'badge-spam',
  review:      'badge bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
  not_trained: 'badge-pending',
  trained:     'badge-safe',
}

const labels = {
  spam:        '🔴 Spam',
  ham:         '✅ Safe',
  safe:        '✅ Safe',
  pending:     '⏳ Pending',
  connected:   '🟢 Connected',
  disconnected:'⚫ Disconnected',
  running:     '🔵 Running',
  completed:   '✅ Completed',
  failed:      '🔴 Failed',
  review:      '⚠️ Review',
  not_trained: '⏳ Not Trained',
  trained:     '✅ Trained',
}

export default function StatusBadge({ status, label, className = '' }) {
  const key = (status || '').toLowerCase()
  return (
    <span className={clsx(variants[key] || 'badge bg-slate-100 text-slate-600', className)}>
      {label || labels[key] || status}
    </span>
  )
}
