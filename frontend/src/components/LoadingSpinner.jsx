import clsx from 'clsx'

export default function LoadingSpinner({ size = 'md', className = '' }) {
  const sizes = {
    xs:  'w-3 h-3 border',
    sm:  'w-5 h-5 border-2',
    md:  'w-8 h-8 border-2',
    lg:  'w-12 h-12 border-3',
    xl:  'w-16 h-16 border-4',
  }
  return (
    <div
      className={clsx(
        sizes[size] || sizes.md,
        'rounded-full border-brand-200 dark:border-brand-800 border-t-brand-600 dark:border-t-brand-400 animate-spin',
        className
      )}
      role="status"
      aria-label="Loading"
    />
  )
}

export function LoadingPage() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4 animate-enter">
      <LoadingSpinner size="lg" />
      <p className="text-sm text-slate-500 dark:text-slate-400 font-medium">Loading…</p>
    </div>
  )
}

export function LoadingOverlay() {
  return (
    <div className="absolute inset-0 flex items-center justify-center bg-white/60 dark:bg-navy-900/60 backdrop-blur-sm rounded-2xl z-10">
      <LoadingSpinner size="md" />
    </div>
  )
}
