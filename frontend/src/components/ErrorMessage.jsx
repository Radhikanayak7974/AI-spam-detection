import { AlertCircle, RefreshCw } from 'lucide-react'

export default function ErrorMessage({ message, onRetry }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-12 px-4 animate-enter">
      <div className="w-12 h-12 rounded-full bg-red-50 dark:bg-red-900/20 flex items-center justify-center">
        <AlertCircle className="w-6 h-6 text-red-500" />
      </div>
      <div className="text-center">
        <p className="font-semibold text-slate-800 dark:text-slate-200 text-sm">Something went wrong</p>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 max-w-xs">{message || 'An unexpected error occurred.'}</p>
      </div>
      {onRetry && (
        <button onClick={onRetry} className="btn-secondary gap-1.5 text-xs mt-1">
          <RefreshCw className="w-3.5 h-3.5" />
          Try again
        </button>
      )}
    </div>
  )
}
