import { useState, useEffect } from 'react'
import {
  TrendingUp, BarChart3, PieChart as PieChartIcon, Activity,
  Database, CheckCircle2, ShieldAlert, ShieldCheck, AlertTriangle,
  Calendar, RefreshCw, Layers, Sparkles, Filter, Mail, Users
} from 'lucide-react'
import {
  LineChart, Line, BarChart, Bar, AreaChart, Area,
  PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer
} from 'recharts'
import { analyticsAPI } from '../services/api'
import LoadingSpinner from '../components/LoadingSpinner'

const PIE_COLORS = ['#ef4444', '#10b981', '#f59e0b']

export default function Analytics() {
  const [dateFilter, setDateFilter] = useState('30d')
  const [customStart, setCustomStart] = useState('')
  const [customEnd, setCustomEnd] = useState('')
  const [trendInterval, setTrendInterval] = useState('daily')

  const [loading, setLoading] = useState(true)
  const [overview, setOverview] = useState(null)
  const [trends, setTrends] = useState([])
  const [sendersData, setSendersData] = useState(null)
  const [patterns, setPatterns] = useState([])
  const [modelComp, setModelComp] = useState(null)

  const fetchAllAnalytics = async () => {
    try {
      setLoading(true)
      const params = {
        filter: dateFilter,
        start_date: dateFilter === 'custom' ? customStart : undefined,
        end_date: dateFilter === 'custom' ? customEnd : undefined,
      }

      const [overviewRes, trendsRes, sendersRes, patternsRes, compRes] = await Promise.all([
        analyticsAPI.overview(params),
        analyticsAPI.trends({ ...params, interval: trendInterval }),
        analyticsAPI.senders(params),
        analyticsAPI.patterns(),
        analyticsAPI.modelComparison(),
      ])

      setOverview(overviewRes.data?.data || null)
      setTrends(trendsRes.data?.data?.trends || [])
      setSendersData(sendersRes.data?.data || null)
      setPatterns(patternsRes.data?.data?.patterns || [])
      setModelComp(compRes.data?.data || null)
    } catch (err) {
      console.error('Failed to load analytics data:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchAllAnalytics()
  }, [dateFilter, trendInterval])

  // Pie chart data
  const pieData = overview ? [
    { name: 'Spam Emails', value: overview.spam_detected },
    { name: 'Safe Emails', value: overview.safe_emails },
    { name: 'Review Required', value: overview.review_required },
  ].filter(d => d.value > 0) : []

  // Test set comparison bar data
  const lrTest = modelComp?.test_dataset_benchmarks?.logistic_regression
  const nbTest = modelComp?.test_dataset_benchmarks?.naive_bayes

  const testBenchmarkData = lrTest && nbTest ? [
    { metric: 'Accuracy',  'Logistic Regression': (lrTest.accuracy * 100).toFixed(1),  'Naive Bayes': (nbTest.accuracy * 100).toFixed(1) },
    { metric: 'Precision', 'Logistic Regression': (lrTest.precision * 100).toFixed(1), 'Naive Bayes': (nbTest.precision * 100).toFixed(1) },
    { metric: 'Recall',    'Logistic Regression': (lrTest.recall * 100).toFixed(1),    'Naive Bayes': (nbTest.recall * 100).toFixed(1) },
    { metric: 'F1-Score',  'Logistic Regression': (lrTest.f1 * 100).toFixed(1),        'Naive Bayes': (nbTest.f1 * 100).toFixed(1) },
    { metric: 'ROC-AUC',   'Logistic Regression': (lrTest.auc * 100).toFixed(1),       'Naive Bayes': (nbTest.auc * 100).toFixed(1) },
  ] : []

  return (
    <div className="space-y-6">
      {/* Header & Date Filter Bar */}
      <div className="card p-5">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-purple-50 dark:bg-purple-900/20 flex items-center justify-center">
              <TrendingUp className="w-5 h-5 text-purple-600 dark:text-purple-400" />
            </div>
            <div>
              <h2 className="font-semibold text-slate-800 dark:text-slate-200">
                Advanced Analytics &amp; Threat Intelligence
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                Real database analytics, time-series classification trends, and ML model comparisons
              </p>
            </div>
          </div>

          {/* Date range filters */}
          <div className="flex flex-wrap items-center gap-2">
            {[
              { id: 'today', label: 'Today' },
              { id: '7d', label: 'Last 7 Days' },
              { id: '30d', label: 'Last 30 Days' },
              { id: '90d', label: 'Last 90 Days' },
              { id: 'all', label: 'All Time' },
              { id: 'custom', label: 'Custom' },
            ].map(({ id, label }) => (
              <button
                key={id}
                onClick={() => setDateFilter(id)}
                className={`text-xs px-3 py-1.5 rounded-lg font-medium transition-all ${
                  dateFilter === id
                    ? 'bg-brand-600 text-white shadow-sm'
                    : 'bg-slate-100 dark:bg-navy-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-navy-700'
                }`}
              >
                {label}
              </button>
            ))}

            <button
              onClick={fetchAllAnalytics}
              title="Refresh Analytics"
              className="btn-secondary text-xs p-1.5 rounded-lg"
            >
              <RefreshCw className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* Custom date range inputs */}
        {dateFilter === 'custom' && (
          <div className="mt-4 pt-3 border-t border-slate-100 dark:border-navy-700/60 flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-2 text-xs">
              <span className="text-slate-500">From:</span>
              <input
                type="date"
                value={customStart}
                onChange={(e) => setCustomStart(e.target.value)}
                className="input py-1 px-2 text-xs"
              />
            </div>
            <div className="flex items-center gap-2 text-xs">
              <span className="text-slate-500">To:</span>
              <input
                type="date"
                value={customEnd}
                onChange={(e) => setCustomEnd(e.target.value)}
                className="input py-1 px-2 text-xs"
              />
            </div>
            <button
              onClick={fetchAllAnalytics}
              className="btn-primary text-xs py-1 px-3"
            >
              Apply Range
            </button>
          </div>
        )}
      </div>

      {loading ? (
        <div className="card p-16 flex justify-center">
          <LoadingSpinner size="lg" message="Computing database analytics and distributions..." />
        </div>
      ) : (
        <>
          {/* Top KPI Cards (Real DB Records) */}
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            <div className="card p-4">
              <p className="text-xs text-slate-500 dark:text-slate-400 font-medium">Emails Analyzed</p>
              <p className="text-2xl font-bold text-slate-900 dark:text-white mt-1">
                {overview?.total_emails_analyzed ?? 0}
              </p>
              <span className="text-[11px] text-slate-400">Total in range</span>
            </div>

            <div className="card p-4">
              <p className="text-xs text-slate-500 dark:text-slate-400 font-medium">Spam Detected</p>
              <p className="text-2xl font-bold text-red-600 dark:text-red-400 mt-1">
                {overview?.spam_detected ?? 0}
              </p>
              <span className="text-[11px] text-red-500 font-semibold">
                {overview?.spam_percentage ?? 0}% of scanned
              </span>
            </div>

            <div className="card p-4">
              <p className="text-xs text-slate-500 dark:text-slate-400 font-medium">Safe Emails</p>
              <p className="text-2xl font-bold text-emerald-600 dark:text-emerald-400 mt-1">
                {overview?.safe_emails ?? 0}
              </p>
              <span className="text-[11px] text-emerald-500 font-semibold">
                {overview?.safe_percentage ?? 0}% of scanned
              </span>
            </div>

            <div className="card p-4">
              <p className="text-xs text-slate-500 dark:text-slate-400 font-medium">Review Required</p>
              <p className="text-2xl font-bold text-amber-600 dark:text-amber-400 mt-1">
                {overview?.review_required ?? 0}
              </p>
              <span className="text-[11px] text-amber-500 font-semibold">
                {overview?.review_percentage ?? 0}% disagreement
              </span>
            </div>

            <div className="card p-4">
              <p className="text-xs text-slate-500 dark:text-slate-400 font-medium">Model Disagreement</p>
              <p className="text-2xl font-bold text-purple-600 dark:text-purple-400 mt-1">
                {overview?.disagreement_rate ?? 0}%
              </p>
              <span className="text-[11px] text-slate-400">
                {overview?.disagreement_count ?? 0} samples
              </span>
            </div>

            <div className="card p-4">
              <p className="text-xs text-slate-500 dark:text-slate-400 font-medium">User Corrections</p>
              <p className="text-2xl font-bold text-blue-600 dark:text-blue-400 mt-1">
                {overview?.corrections_count ?? 0}
              </p>
              <span className="text-[11px] text-slate-400">
                {overview?.total_feedback ?? 0} total feedbacks
              </span>
            </div>
          </div>

          {/* Charts Row 1: Time Series Trends & Spam Activity */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Daily/Weekly Classification Trends (2 Cols) */}
            <div className="card p-5 lg:col-span-2 space-y-3">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div>
                  <h3 className="font-semibold text-slate-800 dark:text-slate-200 text-sm flex items-center gap-2">
                    <Activity className="w-4 h-4 text-brand-600 dark:text-brand-400" />
                    Email Classification Trends Over Time
                  </h3>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                    Spam vs Safe volume based on actual database scans
                  </p>
                </div>
                <div className="flex items-center gap-1 bg-slate-100 dark:bg-navy-800 p-1 rounded-lg self-start">
                  {['daily', 'weekly', 'monthly'].map((intv) => (
                    <button
                      key={intv}
                      onClick={() => setTrendInterval(intv)}
                      className={`text-[11px] px-2.5 py-1 rounded capitalize font-medium transition-all ${
                        trendInterval === intv
                          ? 'bg-white dark:bg-navy-900 text-slate-800 dark:text-white shadow-xs'
                          : 'text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
                      }`}
                    >
                      {intv}
                    </button>
                  ))}
                </div>
              </div>

              <div className="h-64 w-full pt-2">
                {trends.length === 0 ? (
                  <div className="h-full flex items-center justify-center text-xs text-slate-400">
                    No timeline data recorded in selected date range.
                  </div>
                ) : (
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={trends} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" opacity={0.5} />
                      <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                      <YAxis tick={{ fontSize: 11 }} allowDecimals={false} />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: '#1e293b',
                          borderColor: '#334155',
                          borderRadius: '8px',
                          color: '#f8fafc',
                          fontSize: '12px',
                        }}
                      />
                      <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '8px' }} />
                      <Line type="monotone" dataKey="spam" name="Spam" stroke="#ef4444" strokeWidth={2.5} dot={{ r: 3 }} />
                      <Line type="monotone" dataKey="safe" name="Safe" stroke="#10b981" strokeWidth={2.5} dot={{ r: 3 }} />
                      <Line type="monotone" dataKey="review" name="Review" stroke="#f59e0b" strokeWidth={2} strokeDasharray="3 3" />
                    </LineChart>
                  </ResponsiveContainer>
                )}
              </div>
            </div>

            {/* Spam vs Safe Distribution Pie (1 Col) */}
            <div className="card p-5 space-y-3">
              <div>
                <h3 className="font-semibold text-slate-800 dark:text-slate-200 text-sm flex items-center gap-2">
                  <PieChartIcon className="w-4 h-4 text-purple-600 dark:text-purple-400" />
                  Classification Share
                </h3>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                  Proportion of scanned emails
                </p>
              </div>

              <div className="h-64 w-full flex items-center justify-center">
                {pieData.length === 0 ? (
                  <div className="text-xs text-slate-400">No email classifications yet.</div>
                ) : (
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={pieData}
                        cx="50%"
                        cy="45%"
                        innerRadius={50}
                        outerRadius={80}
                        paddingAngle={4}
                        dataKey="value"
                      >
                        {pieData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip
                        contentStyle={{
                          backgroundColor: '#1e293b',
                          borderColor: '#334155',
                          borderRadius: '8px',
                          color: '#f8fafc',
                          fontSize: '12px',
                        }}
                      />
                      <Legend wrapperStyle={{ fontSize: '11px' }} />
                    </PieChart>
                  </ResponsiveContainer>
                )}
              </div>
            </div>
          </div>

          {/* Charts Row 2: Sender Analytics & Spam Patterns */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Top Senders & Top Spam Senders */}
            <div className="card p-5 space-y-4">
              <div>
                <h3 className="font-semibold text-slate-800 dark:text-slate-200 text-sm flex items-center gap-2">
                  <Users className="w-4 h-4 text-brand-600 dark:text-brand-400" />
                  Top Spam Senders &amp; Threat Sources
                </h3>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                  Addresses flagged most frequently by the ML models
                </p>
              </div>

              {sendersData?.top_spam_senders?.length === 0 ? (
                <div className="py-8 text-center text-xs text-slate-400">
                  No spam sender records available in the selected window.
                </div>
              ) : (
                <div className="space-y-2">
                  {sendersData?.top_spam_senders?.map((item, i) => (
                    <div
                      key={i}
                      className="flex items-center justify-between p-2.5 rounded-lg bg-slate-50 dark:bg-navy-800/50 border border-slate-100 dark:border-navy-700/50 text-xs"
                    >
                      <div className="flex items-center gap-2 min-w-0">
                        <span className="w-5 h-5 rounded-full bg-red-100 text-red-700 dark:bg-red-950/40 dark:text-red-400 font-mono text-[10px] font-bold flex items-center justify-center shrink-0">
                          #{i + 1}
                        </span>
                        <span className="font-mono text-slate-800 dark:text-slate-200 truncate max-w-[280px]">
                          {item.sender}
                        </span>
                      </div>
                      <span className="font-bold text-red-600 dark:text-red-400 font-mono text-xs">
                        {item.count} {item.count === 1 ? 'threat' : 'threats'}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Frequently Detected Spam Patterns & Keywords */}
            <div className="card p-5 space-y-4">
              <div>
                <h3 className="font-semibold text-slate-800 dark:text-slate-200 text-sm flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-purple-600 dark:text-purple-400" />
                  Frequently Detected Spam Patterns &amp; Keywords
                </h3>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                  Explainable AI signal words most predictive of spam in your inbox
                </p>
              </div>

              <div className="flex flex-wrap gap-2 pt-2">
                {patterns.length === 0 ? (
                  <div className="text-xs text-slate-400">No discriminative tokens extracted yet.</div>
                ) : (
                  patterns.map((item, idx) => (
                    <span
                      key={idx}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-mono bg-red-50 text-red-800 dark:bg-red-950/30 dark:text-red-300 border border-red-200/60 dark:border-red-900/40"
                    >
                      <span>{item.word}</span>
                      <span className="text-[10px] font-bold px-1.5 py-0.2 rounded-full bg-red-200 dark:bg-red-900/60 text-red-900 dark:text-red-200">
                        {item.count}
                      </span>
                    </span>
                  ))
                )}
              </div>
            </div>
          </div>

          {/* Model Head-to-Head Comparison (Test Set vs Live Gmail) */}
          <div className="card p-5 space-y-4">
            <div>
              <h3 className="font-semibold text-slate-800 dark:text-slate-200 text-sm flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-brand-600 dark:text-brand-400" />
                Dual-Model Head-to-Head Evaluation (Logistic Regression vs Naive Bayes)
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                Clearly distinguishes test-dataset benchmark metrics from live Gmail inbox predictions
              </p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 pt-2">
              {/* Benchmark Bar Chart */}
              <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={testBenchmarkData} margin={{ top: 10, right: 10, left: -15, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" opacity={0.5} />
                    <XAxis dataKey="metric" tick={{ fontSize: 11 }} />
                    <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} unit="%" />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#1e293b',
                        borderColor: '#334155',
                        borderRadius: '8px',
                        color: '#f8fafc',
                        fontSize: '12px',
                      }}
                      formatter={(val) => [`${val}%`]}
                    />
                    <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '8px' }} />
                    <Bar dataKey="Logistic Regression" fill="#4f46e5" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="Naive Bayes" fill="#06b6d4" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>

              {/* Live Gmail Statistics Table */}
              <div className="space-y-3">
                <div className="overflow-x-auto rounded-xl border border-slate-100 dark:border-navy-700/60">
                  <table className="w-full text-xs text-left">
                    <thead className="bg-slate-50 dark:bg-navy-800 text-slate-700 dark:text-slate-300 font-semibold border-b border-slate-100 dark:border-navy-700">
                      <tr>
                        <th className="p-3">Evaluation Metric</th>
                        <th className="p-3">Logistic Regression</th>
                        <th className="p-3">Multinomial Naive Bayes</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 dark:divide-navy-700 font-mono">
                      <tr>
                        <td className="p-3 font-sans font-medium text-slate-800 dark:text-slate-200">
                          Test-Set Accuracy
                        </td>
                        <td className="p-3 text-indigo-600 dark:text-indigo-400 font-bold">
                          {lrTest?.accuracy ? `${(lrTest.accuracy * 100).toFixed(1)}%` : '—'}
                        </td>
                        <td className="p-3 text-cyan-600 dark:text-cyan-400 font-bold">
                          {nbTest?.accuracy ? `${(nbTest.accuracy * 100).toFixed(1)}%` : '—'}
                        </td>
                      </tr>
                      <tr>
                        <td className="p-3 font-sans font-medium text-slate-800 dark:text-slate-200">
                          Test-Set F1-Score
                        </td>
                        <td className="p-3 text-indigo-600 dark:text-indigo-400 font-bold">
                          {lrTest?.f1 ? `${(lrTest.f1 * 100).toFixed(1)}%` : '—'}
                        </td>
                        <td className="p-3 text-cyan-600 dark:text-cyan-400 font-bold">
                          {nbTest?.f1 ? `${(nbTest.f1 * 100).toFixed(1)}%` : '—'}
                        </td>
                      </tr>
                      <tr>
                        <td className="p-3 font-sans font-medium text-slate-800 dark:text-slate-200">
                          Live Spam Detections
                        </td>
                        <td className="p-3 text-slate-700 dark:text-slate-300">
                          {modelComp?.live_gmail_statistics?.logistic_regression_spam_count ?? 0}
                        </td>
                        <td className="p-3 text-slate-700 dark:text-slate-300">
                          {modelComp?.live_gmail_statistics?.naive_bayes_spam_count ?? 0}
                        </td>
                      </tr>
                      <tr>
                        <td className="p-3 font-sans font-medium text-slate-800 dark:text-slate-200">
                          Live Avg Confidence
                        </td>
                        <td className="p-3 text-slate-700 dark:text-slate-300">
                          {modelComp?.live_gmail_statistics?.lr_average_confidence
                            ? `${(modelComp.live_gmail_statistics.lr_average_confidence * 100).toFixed(1)}%`
                            : '—'}
                        </td>
                        <td className="p-3 text-slate-700 dark:text-slate-300">
                          {modelComp?.live_gmail_statistics?.nb_average_confidence
                            ? `${(modelComp.live_gmail_statistics.nb_average_confidence * 100).toFixed(1)}%`
                            : '—'}
                        </td>
                      </tr>
                      <tr>
                        <td className="p-3 font-sans font-medium text-slate-800 dark:text-slate-200">
                          Inter-Model Disagreements
                        </td>
                        <td colSpan={2} className="p-3 text-center text-amber-600 dark:text-amber-400 font-bold">
                          {modelComp?.live_gmail_statistics?.disagreement_count ?? 0} emails ({modelComp?.live_gmail_statistics?.disagreement_rate_percentage ?? 0}%)
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
