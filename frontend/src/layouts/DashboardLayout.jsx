import { useState } from 'react'
import clsx from 'clsx'
import Sidebar from '../components/Sidebar'
import Header from '../components/Header'

export default function DashboardLayout({ children, darkMode, setDarkMode }) {
  const [collapsed,   setCollapsed]   = useState(false)
  const [mobileOpen,  setMobileOpen]  = useState(false)

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-navy-950 font-sans">
      <Sidebar
        collapsed={collapsed}
        onToggle={() => setCollapsed(c => !c)}
        mobileOpen={mobileOpen}
        onMobileClose={() => setMobileOpen(false)}
      />

      <Header
        collapsed={collapsed}
        darkMode={darkMode}
        setDarkMode={setDarkMode}
        onMobileMenuOpen={() => setMobileOpen(true)}
      />

      {/* Main content area – offset by sidebar on desktop */}
      <main
        className={clsx(
          'pt-16 min-h-screen transition-all duration-300',
          collapsed ? 'lg:pl-[72px]' : 'lg:pl-[260px]'
        )}
      >
        <div className="p-4 sm:p-6 max-w-[1600px] mx-auto animate-enter">
          {children}
        </div>
      </main>
    </div>
  )
}
