import clsx from 'clsx'

/**
 * EmptyState – shown when lists/charts have no data.
 */
export default function EmptyState({
  icon: Icon,
  title = 'No data yet',
  description = 'Data will appear here once available.',
  action,
  className = '',
}) {
  return (
    <div className={clsx('flex flex-col items-center justify-center gap-4 py-16 px-4 text-center animate-enter', className)}>
      {Icon && (
        <div className="w-16 h-16 rounded-2xl bg-slate-100 dark:bg-navy-700 flex items-center justify-center">
          <Icon className="w-8 h-8 text-slate-400 dark:text-slate-500" />
        </div>
      )}
      <div>
        <p className="font-semibold text-slate-700 dark:text-slate-300 text-base">{title}</p>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-1 max-w-sm">{description}</p>
      </div>
      {action && (
        <div className="mt-1">
          {action}
        </div>
      )}
    </div>
  )
}
