import clsx from 'clsx'
import LoadingSpinner from './LoadingSpinner'

/**
 * StatisticCard – dashboard KPI card.
 */
export default function StatisticCard({
  title,
  value,
  subtitle,
  icon: Icon,
  iconColor = 'brand',
  trend,        // { value: number, label: string, up: bool }
  loading = false,
  className = '',
}) {
  const iconBg = {
    brand:   'bg-brand-50   dark:bg-brand-900/20 text-brand-600   dark:text-brand-400',
    red:     'bg-red-50     dark:bg-red-900/20   text-red-500     dark:text-red-400',
    emerald: 'bg-emerald-50 dark:bg-emerald-900/20 text-emerald-600 dark:text-emerald-400',
    amber:   'bg-amber-50   dark:bg-amber-900/20 text-amber-600   dark:text-amber-400',
    purple:  'bg-purple-50  dark:bg-purple-900/20 text-purple-600  dark:text-purple-400',
    slate:   'bg-slate-100  dark:bg-slate-800    text-slate-500   dark:text-slate-400',
  }

  return (
    <div className={clsx('card p-5 flex flex-col gap-4 hover:shadow-md transition-shadow duration-200', className)}>
      <div className="flex items-start justify-between">
        <p className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">{title}</p>
        {Icon && (
          <div className={clsx('w-9 h-9 rounded-xl flex items-center justify-center shrink-0', iconBg[iconColor] || iconBg.brand)}>
            <Icon className="w-4.5 h-4.5" style={{ width: '1.1rem', height: '1.1rem' }} />
          </div>
        )}
      </div>

      <div>
        {loading ? (
          <div className="flex items-center gap-2 h-9">
            <LoadingSpinner size="sm" />
          </div>
        ) : (
          <p className="text-2xl font-bold text-slate-900 dark:text-slate-100 tracking-tight leading-none truncate">
            {value ?? '—'}
          </p>
        )}
        {subtitle && (
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1.5">{subtitle}</p>
        )}
      </div>

      {trend && (
        <div className={clsx(
          'inline-flex items-center gap-1 text-xs font-medium',
          trend.up ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-500 dark:text-red-400'
        )}>
          <span>{trend.up ? '↑' : '↓'}</span>
          <span>{trend.value}</span>
          <span className="text-slate-500 dark:text-slate-400 font-normal">{trend.label}</span>
        </div>
      )}
    </div>
  )
}
