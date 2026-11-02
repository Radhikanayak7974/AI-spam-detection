import React from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { Sun, Moon, Menu, Bell, Activity, LogOut } from 'lucide-react'
import clsx from 'clsx'
import { useAuth } from '../context/AuthContext'

const PAGE_TITLES = {
  '/overview':          { title: 'Overview',          subtitle: 'Dashboard & system status' },
  '/inbox':             { title: 'Gmail Inbox',        subtitle: 'Your synced emails' },
  '/spam':              { title: 'Spam Emails',        subtitle: 'Detected spam messages' },
  '/safe':              { title: 'Safe Emails',        subtitle: 'Verified safe messages' },
  '/model-performance': { title: 'Model Performance',  subtitle: 'ML model metrics & evaluation' },
  '/analytics':         { title: 'Analytics',          subtitle: 'Trends & insights' },
  '/settings':          { title: 'Settings',           subtitle: 'Application configuration' },
}

export default function Header({ collapsed, darkMode, setDarkMode, onMobileMenuOpen }) {
  const { pathname } = useLocation()
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const page = PAGE_TITLES[pathname] || { title: 'SpamGuard AI', subtitle: '' }

  const handleSignOut = async () => {
    await logout()
    navigate('/')
  }

  return (
    <header className={clsx(
      'fixed top-0 right-0 h-16 z-20 flex items-center px-4 gap-4',
      'bg-white/80 dark:bg-navy-900/80 backdrop-blur-md',
      'border-b border-slate-100 dark:border-navy-700/60',
      'transition-all duration-300',
      // Offset by sidebar width on desktop
      collapsed ? 'lg:left-[72px]' : 'lg:left-[260px]',
      'left-0'
    )}>
      {/* Mobile hamburger */}
      <button
        id="mobile-menu-btn"
        onClick={onMobileMenuOpen}
        className="btn-ghost p-2 lg:hidden"
        aria-label="Open menu"
      >
        <Menu className="w-5 h-5" />
      </button>

      {/* Page title */}
      <div className="flex-1 min-w-0">
        <h1 className="font-bold text-slate-900 dark:text-slate-100 text-base leading-none truncate">
          {page.title}
        </h1>
        {page.subtitle && (
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5 truncate hidden sm:block">
            {page.subtitle}
          </p>
        )}
      </div>

      {/* Right controls */}
      <div className="flex items-center gap-1">
        {/* Backend status indicator */}
        <BackendStatus />

        {/* Notification bell */}
        <button
          id="notification-btn"
          className="btn-ghost p-2 relative"
          aria-label="Notifications"
        >
          <Bell className="w-4.5 h-4.5" style={{ width: '1.1rem', height: '1.1rem' }} />
        </button>

        {/* Dark mode toggle */}
        <button
          id="dark-mode-toggle"
          onClick={() => setDarkMode(!darkMode)}
          className="btn-ghost p-2"
          aria-label="Toggle dark mode"
        >
          {darkMode
            ? <Sun  className="w-4.5 h-4.5 text-amber-500" style={{ width: '1.1rem', height: '1.1rem' }} />
            : <Moon className="w-4.5 h-4.5" style={{ width: '1.1rem', height: '1.1rem' }} />
          }
        </button>

        {/* User Pill & Sign Out */}
        {user && (
          <div className="flex items-center gap-2 ml-2 pl-2 border-l border-slate-200 dark:border-navy-700/60">
            <div className="w-7 h-7 rounded-lg bg-gradient-to-tr from-brand-600 via-purple-600 to-indigo-600 flex items-center justify-center text-white text-xs font-bold shadow-sm">
              {user.name ? user.name[0].toUpperCase() : 'U'}
            </div>
            <span className="text-xs font-medium text-slate-700 dark:text-slate-300 hidden md:block max-w-[120px] truncate">
              {user.name || user.email}
            </span>
            <button
              onClick={handleSignOut}
              className="btn-ghost p-1.5 text-slate-400 hover:text-red-500 transition-colors"
              title="Sign Out"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>
    </header>
  )
}

/** Small dot that polls /api/health to show backend connectivity */
function BackendStatus() {
  const [status, setStatus] = React.useState('checking') // 'online' | 'offline' | 'checking'

  React.useEffect(() => {
    let mounted = true
    const check = async () => {
      try {
        const res = await fetch('/api/health', { signal: AbortSignal.timeout(3000) })
        if (mounted) setStatus(res.ok ? 'online' : 'offline')
      } catch {
        if (mounted) setStatus('offline')
      }
    }
    check()
    const id = setInterval(check, 30000)
    return () => { mounted = false; clearInterval(id) }
  }, [])

  return (
    <div
      className="btn-ghost p-2 flex items-center gap-1.5 text-xs font-medium cursor-default"
      title={`Backend: ${status}`}
    >
      <Activity className="w-3.5 h-3.5 text-slate-400" />
      <span
        className={clsx(
          'w-1.5 h-1.5 rounded-full',
          status === 'online'   && 'bg-emerald-500',
          status === 'offline'  && 'bg-red-500',
          status === 'checking' && 'bg-amber-400 animate-pulse',
        )}
      />
    </div>
  )
}


