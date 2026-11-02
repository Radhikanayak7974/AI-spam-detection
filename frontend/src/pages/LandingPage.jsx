import { Link } from 'react-router-dom'
import {
  ShieldCheck,
  Zap,
  Inbox,
  BarChart3,
  Lock,
  RefreshCw,
  Cpu,
  ArrowRight,
  CheckCircle2,
  Sparkles,
  Server,
  Layers,
  Database,
  ExternalLink,
  ChevronRight,
  ShieldAlert,
} from 'lucide-react'
import { useAuth } from '../context/AuthContext'

export default function LandingPage() {
  const { isAuthenticated } = useAuth()

  return (
    <div className="min-h-screen bg-[#070A13] text-slate-100 font-sans selection:bg-purple-500 selection:text-white relative overflow-hidden">
      {/* Background ambient gradient glow blobs */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[1000px] h-[550px] bg-gradient-to-tr from-purple-700/20 via-blue-600/15 to-transparent blur-3xl pointer-events-none rounded-full" />
      <div className="absolute top-[600px] -left-48 w-96 h-96 bg-blue-600/10 blur-[120px] pointer-events-none rounded-full" />
      <div className="absolute top-[900px] -right-48 w-96 h-96 bg-purple-600/10 blur-[120px] pointer-events-none rounded-full" />

      {/* ── Navigation Bar ────────────────────────────────────────── */}
      <header className="sticky top-0 z-50 backdrop-blur-xl bg-[#070A13]/80 border-b border-slate-800/60">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-20 flex items-center justify-between">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-3 group">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-brand-500 via-purple-600 to-indigo-600 flex items-center justify-center shadow-lg shadow-purple-500/25 group-hover:shadow-purple-500/40 transition-all duration-300">
              <Zap className="w-5 h-5 text-white" />
            </div>
            <div>
              <span className="text-xl font-bold tracking-tight bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
                SpamGuard
              </span>
              <span className="text-xs ml-1.5 font-semibold text-purple-400 uppercase tracking-widest px-1.5 py-0.5 rounded bg-purple-500/10 border border-purple-500/20">
                AI
              </span>
            </div>
          </Link>

          {/* Desktop Nav Links */}
          <nav className="hidden md:flex items-center gap-8 text-sm font-medium text-slate-300">
            <a href="#features" className="hover:text-white transition-colors">Features</a>
            <a href="#how-it-works" className="hover:text-white transition-colors">How It Works</a>
            <a href="#metrics" className="hover:text-white transition-colors">AI Models</a>
            <a href="#technology" className="hover:text-white transition-colors">Tech Stack</a>
          </nav>

          {/* Auth Action Buttons */}
          <div className="flex items-center gap-3">
            {isAuthenticated ? (
              <Link
                to="/overview"
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold text-white bg-gradient-to-r from-brand-600 via-purple-600 to-indigo-600 hover:from-brand-500 hover:to-indigo-500 shadow-lg shadow-purple-500/25 transition-all duration-300"
              >
                Go to Dashboard
                <ArrowRight className="w-4 h-4" />
              </Link>
            ) : (
              <>
                <Link
                  to="/login"
                  className="px-4 py-2 text-sm font-medium text-slate-300 hover:text-white transition-colors"
                >
                  Sign In
                </Link>
                <Link
                  to="/register"
                  className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold text-white bg-gradient-to-r from-brand-600 via-purple-600 to-indigo-600 hover:from-brand-500 hover:to-indigo-500 shadow-lg shadow-purple-500/25 hover:shadow-purple-500/40 hover:-translate-y-0.5 transition-all duration-300"
                >
                  Get Started
                  <ArrowRight className="w-4 h-4" />
                </Link>
              </>
            )}
          </div>
        </div>
      </header>

      {/* ── Hero Section ──────────────────────────────────────────── */}
      <section className="relative pt-20 pb-24 md:pt-28 md:pb-32 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto text-center">
        {/* Pill Badge */}
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-purple-500/10 border border-purple-500/25 text-purple-300 text-xs sm:text-sm font-medium mb-8 backdrop-blur-md animate-fade-in shadow-inner">
          <Sparkles className="w-4 h-4 text-purple-400" />
          <span>Powered by Production Enron Corpus — 98.83% Detection Accuracy</span>
          <ChevronRight className="w-3.5 h-3.5 text-purple-400" />
        </div>

        {/* Hero Title */}
        <h1 className="text-4xl sm:text-6xl lg:text-7xl font-extrabold tracking-tight text-white leading-[1.1] max-w-4xl mx-auto">
          Your Inbox.{' '}
          <span className="bg-gradient-to-r from-blue-400 via-purple-400 to-indigo-300 bg-clip-text text-transparent">
            Smarter. Safer.
          </span>
        </h1>

        {/* Hero Subtitle */}
        <p className="mt-6 text-lg sm:text-xl text-slate-400 max-w-2xl mx-auto leading-relaxed">
          SpamGuard AI combines real-time Gmail synchronization with high-precision machine learning
          algorithms to neutralize phishing, scams, and unsolicited spam before they reach your focus.
        </p>

        {/* Hero CTAs */}
        <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
          <Link
            to="/register"
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2.5 px-8 py-3.5 rounded-xl font-semibold text-white bg-gradient-to-r from-brand-600 via-purple-600 to-indigo-600 hover:from-brand-500 hover:to-indigo-500 shadow-xl shadow-purple-600/25 hover:shadow-purple-600/40 hover:-translate-y-0.5 transition-all text-base"
          >
            Get Started Free
            <ArrowRight className="w-4 h-4" />
          </Link>
          <Link
            to="/login"
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-8 py-3.5 rounded-xl font-semibold text-slate-300 bg-slate-900/80 hover:bg-slate-800 border border-slate-800 hover:border-slate-700 hover:text-white transition-all text-base backdrop-blur-md"
          >
            Sign In to Dashboard
          </Link>
        </div>

        {/* Trust Badges */}
        <div className="mt-12 flex flex-wrap items-center justify-center gap-6 text-xs sm:text-sm text-slate-400 font-medium">
          <span className="flex items-center gap-1.5">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" /> Read-Only Gmail OAuth 2.0
          </span>
          <span className="flex items-center gap-1.5">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" /> Dual-Voting Ensemble ML
          </span>
          <span className="flex items-center gap-1.5">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" /> 100% Localhost Privacy
          </span>
        </div>

        {/* ── Interactive Hero Preview Mockup ─────────────────────── */}
        <div className="mt-16 relative max-w-5xl mx-auto">
          <div className="relative rounded-2xl p-1 bg-gradient-to-b from-purple-500/30 via-slate-800/40 to-slate-900/80 shadow-2xl shadow-purple-900/20">
            <div className="rounded-[14px] bg-[#0B0F1D] border border-slate-800/80 p-5 sm:p-7 text-left overflow-hidden">
              {/* Top bar mockup */}
              <div className="flex items-center justify-between pb-4 border-b border-slate-800/80">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-red-500/80" />
                  <div className="w-3 h-3 rounded-full bg-amber-500/80" />
                  <div className="w-3 h-3 rounded-full bg-emerald-500/80" />
                  <span className="text-xs font-mono text-slate-500 ml-3">SpamGuard Live Security Monitor v7</span>
                </div>
                <div className="flex items-center gap-2 text-xs">
                  <span className="inline-block w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
                  <span className="text-emerald-400 font-medium">Active Protection: Online</span>
                </div>
              </div>

              {/* Live email triage sample cards */}
              <div className="mt-5 space-y-3">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 hover:border-slate-700 transition-colors gap-3">
                  <div className="flex items-start gap-3">
                    <div className="w-9 h-9 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center shrink-0 mt-0.5">
                      <ShieldCheck className="w-5 h-5 text-emerald-400" />
                    </div>
                    <div>
                      <p className="text-sm font-semibold text-slate-200">Q4 Financial Review & Strategy Sync</p>
                      <p className="text-xs text-slate-400">Attached preliminary revenue figures for Tuesday sync meeting.</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 sm:self-center">
                    <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">
                      SAFE (99.5%)
                    </span>
                  </div>
                </div>

                <div className="flex flex-col sm:flex-row sm:items-center justify-between p-3.5 rounded-xl bg-slate-900/90 border border-red-500/20 hover:border-red-500/30 transition-colors gap-3">
                  <div className="flex items-start gap-3">
                    <div className="w-9 h-9 rounded-lg bg-red-500/10 border border-red-500/20 flex items-center justify-center shrink-0 mt-0.5">
                      <ShieldAlert className="w-5 h-5 text-red-400" />
                    </div>
                    <div>
                      <p className="text-sm font-semibold text-slate-200">URGENT: Claim $1,500,000 International Sweepstakes Payout</p>
                      <p className="text-xs text-slate-400">Claims agent contact required with passport and banking details.</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 sm:self-center">
                    <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-red-500/15 text-red-300 border border-red-500/30">
                      SPAM (99.8%)
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Key Metrics Section ───────────────────────────────────── */}
      <section id="metrics" className="py-16 border-y border-slate-800/80 bg-slate-950/40 relative">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-8 text-center">
            <div className="p-4">
              <p className="text-4xl sm:text-5xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-400">
                98.83%
              </p>
              <p className="mt-2 text-sm font-medium text-slate-400">Logistic Regression Accuracy</p>
            </div>
            <div className="p-4">
              <p className="text-4xl sm:text-5xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-indigo-400">
                98.33%
              </p>
              <p className="mt-2 text-sm font-medium text-slate-400">Multinomial Naive Bayes</p>
            </div>
            <div className="p-4">
              <p className="text-4xl sm:text-5xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-blue-400">
                30,462
              </p>
              <p className="mt-2 text-sm font-medium text-slate-400">Enron Email Corpus Cleaned</p>
            </div>
            <div className="p-4">
              <p className="text-4xl sm:text-5xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-teal-400">
                &lt; 0.2s
              </p>
              <p className="mt-2 text-sm font-medium text-slate-400">Inference Classification Speed</p>
            </div>
          </div>
        </div>
      </section>

      {/* ── Features Section ──────────────────────────────────────── */}
      <section id="features" className="py-24 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="text-xs sm:text-sm font-bold uppercase tracking-widest text-purple-400 mb-3">
            Core Capabilities
          </h2>
          <p className="text-3xl sm:text-4xl font-bold text-white tracking-tight">
            Engineered for High-Precision Email Security
          </p>
          <p className="mt-4 text-slate-400 text-base sm:text-lg">
            Five core layers of machine learning defense designed to keep corporate and personal communication safe.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* Feature 1 */}
          <div className="p-7 rounded-2xl bg-slate-900/70 border border-slate-800/80 hover:border-purple-500/40 transition-all duration-300 group hover:-translate-y-1">
            <div className="w-12 h-12 rounded-xl bg-purple-500/10 border border-purple-500/25 flex items-center justify-center text-purple-400 mb-5 group-hover:scale-110 transition-transform">
              <Cpu className="w-6 h-6" />
            </div>
            <h3 className="text-xl font-bold text-white mb-2">AI Spam Detection</h3>
            <p className="text-sm text-slate-400 leading-relaxed">
              Dual-model ensemble featuring Logistic Regression and Multinomial Naive Bayes trained on 10,000 unigram and bigram TF-IDF n-grams.
            </p>
          </div>

          {/* Feature 2 */}
          <div className="p-7 rounded-2xl bg-slate-900/70 border border-slate-800/80 hover:border-brand-500/40 transition-all duration-300 group hover:-translate-y-1">
            <div className="w-12 h-12 rounded-xl bg-blue-500/10 border border-blue-500/25 flex items-center justify-center text-blue-400 mb-5 group-hover:scale-110 transition-transform">
              <Inbox className="w-6 h-6" />
            </div>
            <h3 className="text-xl font-bold text-white mb-2">Gmail Integration</h3>
            <p className="text-sm text-slate-400 leading-relaxed">
              Connect your Google Gmail account securely using read-only OAuth 2.0 PKCE authentication with incremental 30s background sync.
            </p>
          </div>

          {/* Feature 3 */}
          <div className="p-7 rounded-2xl bg-slate-900/70 border border-slate-800/80 hover:border-indigo-500/40 transition-all duration-300 group hover:-translate-y-1">
            <div className="w-12 h-12 rounded-xl bg-indigo-500/10 border border-indigo-500/25 flex items-center justify-center text-indigo-400 mb-5 group-hover:scale-110 transition-transform">
              <Zap className="w-6 h-6" />
            </div>
            <h3 className="text-xl font-bold text-white mb-2">Real-Time Classification</h3>
            <p className="text-sm text-slate-400 leading-relaxed">
              Instant email scoring with probabilistic confidence breakdowns, identifying high-risk phishing vectors and spam signals on receipt.
            </p>
          </div>

          {/* Feature 4 */}
          <div className="p-7 rounded-2xl bg-slate-900/70 border border-slate-800/80 hover:border-emerald-500/40 transition-all duration-300 group hover:-translate-y-1">
            <div className="w-12 h-12 rounded-xl bg-emerald-500/10 border border-emerald-500/25 flex items-center justify-center text-emerald-400 mb-5 group-hover:scale-110 transition-transform">
              <Lock className="w-6 h-6" />
            </div>
            <h3 className="text-xl font-bold text-white mb-2">Secure Email Management</h3>
            <p className="text-sm text-slate-400 leading-relaxed">
              Triage quarantined spam messages, review borderline classifications, and safeguard your legitimate inbox in a dedicated UI.
            </p>
          </div>

          {/* Feature 5 */}
          <div className="p-7 rounded-2xl bg-slate-900/70 border border-slate-800/80 hover:border-purple-500/40 transition-all duration-300 group hover:-translate-y-1">
            <div className="w-12 h-12 rounded-xl bg-purple-500/10 border border-purple-500/25 flex items-center justify-center text-purple-400 mb-5 group-hover:scale-110 transition-transform">
              <BarChart3 className="w-6 h-6" />
            </div>
            <h3 className="text-xl font-bold text-white mb-2">ML Analytics & Feedback</h3>
            <p className="text-sm text-slate-400 leading-relaxed">
              Interactive confusion matrices, ROC-AUC curves, and automated active learning feedback loops that retrain candidate models continuously.
            </p>
          </div>

          {/* Feature 6 */}
          <div className="p-7 rounded-2xl bg-slate-900/70 border border-slate-800/80 hover:border-blue-500/40 transition-all duration-300 group hover:-translate-y-1">
            <div className="w-12 h-12 rounded-xl bg-blue-500/10 border border-blue-500/25 flex items-center justify-center text-blue-400 mb-5 group-hover:scale-110 transition-transform">
              <RefreshCw className="w-6 h-6" />
            </div>
            <h3 className="text-xl font-bold text-white mb-2">Controlled Versioning</h3>
            <p className="text-sm text-slate-400 leading-relaxed">
              Built-in version control system (`v1` through `v7`) guaranteeing rollback safety, model promotion gates, and full audit logging.
            </p>
          </div>
        </div>
      </section>

      {/* ── How It Works Section ─────────────────────────────────── */}
      <section id="how-it-works" className="py-24 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto border-t border-slate-800/80">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="text-xs sm:text-sm font-bold uppercase tracking-widest text-purple-400 mb-3">
            Workflow
          </h2>
          <p className="text-3xl sm:text-4xl font-bold text-white tracking-tight">
            How SpamGuard Protects You in 3 Steps
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="p-6 rounded-2xl bg-slate-900/40 border border-slate-800/80 relative">
            <span className="text-5xl font-black text-purple-500/20 absolute top-4 right-5">01</span>
            <div className="w-10 h-10 rounded-lg bg-purple-500/15 text-purple-400 flex items-center justify-center font-bold text-sm mb-4">
              1
            </div>
            <h3 className="text-lg font-bold text-white mb-2">Connect Your Inbox</h3>
            <p className="text-sm text-slate-400">
              Sign in to SpamGuard and authorize read-only access to your Gmail account via Google OAuth 2.0 with one click.
            </p>
          </div>

          <div className="p-6 rounded-2xl bg-slate-900/40 border border-slate-800/80 relative">
            <span className="text-5xl font-black text-blue-500/20 absolute top-4 right-5">02</span>
            <div className="w-10 h-10 rounded-lg bg-blue-500/15 text-blue-400 flex items-center justify-center font-bold text-sm mb-4">
              2
            </div>
            <h3 className="text-lg font-bold text-white mb-2">Dual AI Inspection</h3>
            <p className="text-sm text-slate-400">
              Incoming emails pass through TF-IDF feature extractors and dual ensemble classifiers (Logistic Regression + Naive Bayes).
            </p>
          </div>

          <div className="p-6 rounded-2xl bg-slate-900/40 border border-slate-800/80 relative">
            <span className="text-5xl font-black text-indigo-500/20 absolute top-4 right-5">03</span>
            <div className="w-10 h-10 rounded-lg bg-indigo-500/15 text-indigo-400 flex items-center justify-center font-bold text-sm mb-4">
              3
            </div>
            <h3 className="text-lg font-bold text-white mb-2">Automated Triage</h3>
            <p className="text-sm text-slate-400">
              Safe emails are routed to your focus inbox, malicious messages are quarantined, and feedback retrains your personal models.
            </p>
          </div>
        </div>
      </section>

      {/* ── Technology Stack Section ──────────────────────────────── */}
      <section id="technology" className="py-20 border-t border-slate-800/80 bg-slate-950/60">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-xs sm:text-sm font-bold uppercase tracking-widest text-slate-500 mb-6">
            Built with Modern Architecture
          </h2>
          <div className="flex flex-wrap items-center justify-center gap-8 sm:gap-14 text-sm font-semibold text-slate-400">
            <span className="flex items-center gap-2"><Layers className="w-4 h-4 text-blue-400" /> React 18 & Vite</span>
            <span className="flex items-center gap-2"><Server className="w-4 h-4 text-purple-400" /> Python Flask REST API</span>
            <span className="flex items-center gap-2"><Cpu className="w-4 h-4 text-indigo-400" /> Scikit-learn & TF-IDF</span>
            <span className="flex items-center gap-2"><Database className="w-4 h-4 text-emerald-400" /> SQLite Database</span>
            <span className="flex items-center gap-2"><Lock className="w-4 h-4 text-amber-400" /> Google OAuth 2.0 PKCE</span>
          </div>
        </div>
      </section>

      {/* ── Footer ────────────────────────────────────────────────── */}
      <footer className="border-t border-slate-800/80 py-12 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-6 text-sm text-slate-500">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-brand-500 to-purple-600 flex items-center justify-center">
            <Zap className="w-4 h-4 text-white" />
          </div>
          <span className="font-bold text-slate-300">SpamGuard AI</span>
          <span>© 2026. All rights reserved.</span>
        </div>
        <div className="flex items-center gap-6">
          <Link to="/login" className="hover:text-slate-300 transition-colors">Sign In</Link>
          <Link to="/register" className="hover:text-slate-300 transition-colors">Sign Up</Link>
          <Link to="/overview" className="hover:text-slate-300 transition-colors">Dashboard</Link>
        </div>
      </footer>
    </div>
  )
}

