import { NavLink, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard, Inbox, ShieldAlert, ShieldCheck,
  BarChart3, TrendingUp, Settings, ChevronLeft, ChevronRight,
  Zap, X, MessageSquare, LogOut, User
} from 'lucide-react'
import clsx from 'clsx'
import { useAuth } from '../context/AuthContext'

const navItems = [
  { path: '/overview',          label: 'Overview',          icon: LayoutDashboard },
  { path: '/inbox',             label: 'Gmail Inbox',       icon: Inbox },
  { path: '/spam',              label: 'Spam Emails',       icon: ShieldAlert },
  { path: '/safe',              label: 'Safe Emails',       icon: ShieldCheck },
  { path: '/feedback',          label: 'User Feedback',     icon: MessageSquare },
  { path: '/model-performance', label: 'Model Performance', icon: BarChart3 },
  { path: '/analytics',         label: 'Analytics',         icon: TrendingUp },
]

const bottomItems = [
  { path: '/settings', label: 'Settings', icon: Settings },
]

export default function Sidebar({ collapsed, onToggle, mobileOpen, onMobileClose }) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleSignOut = async () => {
    await logout()
    navigate('/')
  }
  return (
    <>
      {/* Mobile overlay */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/40 backdrop-blur-sm lg:hidden"
          onClick={onMobileClose}
        />
      )}

      {/* Sidebar panel */}
      <aside
        className={clsx(
          'fixed top-0 left-0 h-full z-40 flex flex-col',
          'bg-white dark:bg-navy-900 border-r border-slate-100 dark:border-navy-700/60',
          'transition-all duration-300 ease-in-out',
          // Desktop
          'hidden lg:flex',
          collapsed ? 'w-[72px]' : 'w-[260px]',
          // Mobile
          'lg:translate-x-0',
          mobileOpen
            ? '!flex translate-x-0 w-[260px]'
            : '-translate-x-full lg:translate-x-0'
        )}
        style={{ willChange: 'width' }}
      >
        {/* Logo */}
        <div className={clsx(
          'flex items-center h-16 px-4 border-b border-slate-100 dark:border-navy-700/60 shrink-0',
          collapsed ? 'justify-center' : 'justify-between'
        )}>
          <div className="flex items-center gap-2.5 min-w-0">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-brand-500 to-purple-600 flex items-center justify-center shrink-0 shadow-sm">
              <Zap className="w-4 h-4 text-white" />
            </div>
            {!collapsed && (
              <div className="min-w-0">
                <p className="font-bold text-slate-900 dark:text-white text-sm leading-none truncate">SpamGuard</p>
                <p className="text-[10px] text-slate-500 dark:text-slate-400 mt-0.5 font-medium">AI Email Security</p>
              </div>
            )}
          </div>
          {/* Mobile close */}
          {mobileOpen && (
            <button onClick={onMobileClose} className="btn-ghost p-1.5 lg:hidden">
              <X className="w-4 h-4" />
            </button>
          )}
        </div>

        {/* Nav items */}
        <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-0.5">
          {navItems.map(({ path, label, icon: Icon }) => (
            <NavLink
              key={path}
              to={path}
              onClick={onMobileClose}
              className={({ isActive }) =>
                clsx(
                  isActive ? 'nav-item-active' : 'nav-item',
                  collapsed && 'justify-center px-0 py-2.5',
                )
              }
              title={collapsed ? label : undefined}
            >
              <Icon className="w-4.5 h-4.5 shrink-0" style={{ width: '1.1rem', height: '1.1rem' }} />
              {!collapsed && <span className="truncate">{label}</span>}
            </NavLink>
          ))}
        </nav>

        {/* Bottom items & User Profile */}
        <div className="px-3 pb-4 space-y-1 border-t border-slate-100 dark:border-navy-700/60 pt-3 shrink-0">
          {/* User profile card */}
          {user && (
            <div className={clsx(
              "flex items-center gap-2.5 p-2 mb-2 rounded-xl bg-slate-50 dark:bg-navy-800/60 border border-slate-100 dark:border-navy-700/50",
              collapsed && "justify-center p-1.5"
            )}>
              <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-brand-600 via-purple-600 to-indigo-600 flex items-center justify-center text-white font-bold text-xs shrink-0 shadow-sm">
                {user.name ? user.name[0].toUpperCase() : 'U'}
              </div>
              {!collapsed && (
                <div className="min-w-0 flex-1">
                  <p className="text-xs font-semibold text-slate-800 dark:text-slate-100 truncate">{user.name || 'SpamGuard User'}</p>
                  <p className="text-[10px] text-slate-500 dark:text-slate-400 truncate">{user.email}</p>
                </div>
              )}
            </div>
          )}

          {bottomItems.map(({ path, label, icon: Icon }) => (
            <NavLink
              key={path}
              to={path}
              onClick={onMobileClose}
              className={({ isActive }) =>
                clsx(
                  isActive ? 'nav-item-active' : 'nav-item',
                  collapsed && 'justify-center px-0 py-2.5',
                )
              }
              title={collapsed ? label : undefined}
            >
              <Icon className="w-4 h-4 shrink-0" />
              {!collapsed && <span className="truncate">{label}</span>}
            </NavLink>
          ))}

          {/* Sign Out Button */}
          <button
            onClick={handleSignOut}
            className={clsx(
              'nav-item w-full text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-950/30 hover:text-red-700 dark:hover:text-red-300 transition-colors',
              collapsed && 'justify-center px-0 py-2.5'
            )}
            title={collapsed ? 'Sign Out' : undefined}
          >
            <LogOut className="w-4 h-4 shrink-0" />
            {!collapsed && <span className="truncate text-xs font-semibold">Sign Out</span>}
          </button>

          {/* Collapse toggle – desktop only */}
          <button
            id="sidebar-collapse-btn"
            onClick={onToggle}
            className={clsx('nav-item w-full hidden lg:flex text-slate-500 dark:text-slate-400', collapsed && 'justify-center px-0 py-2.5')}
            title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {collapsed
              ? <ChevronRight className="w-4 h-4 shrink-0" />
              : <>
                  <ChevronLeft className="w-4 h-4 shrink-0" />
                  <span className="truncate text-xs">Collapse</span>
                </>
            }
          </button>
        </div>
      </aside>
    </>
  )
}
