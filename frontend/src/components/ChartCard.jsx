import clsx from 'clsx'
import LoadingSpinner from './LoadingSpinner'

/**
 * ChartCard – wrapper for recharts charts with loading/empty states.
 */
export default function ChartCard({
  title,
  description,
  children,
  loading = false,
  empty = false,
  emptyIcon: EmptyIcon,
  emptyText = 'No chart data available yet.',
  className = '',
  headerRight,
}) {
  return (
    <div className={clsx('card p-5 flex flex-col gap-4', className)}>
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="font-semibold text-slate-800 dark:text-slate-200 text-sm">{title}</h3>
          {description && (
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">{description}</p>
          )}
        </div>
        {headerRight && <div className="shrink-0">{headerRight}</div>}
      </div>

      <div className="relative min-h-[180px] flex items-center justify-center">
        {loading ? (
          <LoadingSpinner size="md" />
        ) : empty ? (
          <div className="flex flex-col items-center gap-3 text-center py-6">
            {EmptyIcon && (
              <div className="w-12 h-12 rounded-xl bg-slate-50 dark:bg-navy-700 flex items-center justify-center">
                <EmptyIcon className="w-6 h-6 text-slate-400 dark:text-slate-500" />
              </div>
            )}
            <p className="text-xs text-slate-500 dark:text-slate-400 max-w-[200px]">{emptyText}</p>
            <p className="text-[10px] text-slate-400 dark:text-slate-500">Charts will populate after Gmail sync</p>
          </div>
        ) : (
          <div className="w-full">{children}</div>
        )}
      </div>
    </div>
  )
}
