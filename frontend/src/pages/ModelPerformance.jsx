import { useState, useEffect } from 'react'
import {
  Brain,
  BarChart3,
  FlaskConical,
  RefreshCw,
  Send,
  Sparkles,
  CheckCircle2,
  AlertTriangle,
  Database,
  Layers,
  ArrowRight,
  TrendingUp,
  ShieldCheck,
  ShieldAlert,
  Clock,
  History,
  Activity,
  Check,
  X
} from 'lucide-react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import { modelsAPI } from '../services/api'
import StatusBadge from '../components/StatusBadge'
import LoadingSpinner from '../components/LoadingSpinner'

const SAMPLE_PRESETS = [
  {
    label: '🚨 Bank Phishing Alert',
    model: 'logistic_regression',
    text: 'URGENT: Your account at Chase Bank has been suspended due to unauthorized access. Click http://bank-verification-portal.xyz/login immediately to verify your identity and restore full access.',
  },
  {
    label: '🎁 Sweepstakes Winner',
    model: 'naive_bayes',
    text: 'Congratulations! You have been selected as the grand winner of our 2026 international sweepstakes prize of $2,500,000. Call +1-800-482-9182 immediately to claim your certified cashier check.',
  },
  {
    label: '💼 Team Sprint Planning',
    model: 'logistic_regression',
    text: 'Hi team, just a reminder that our weekly sprint planning meeting is scheduled for tomorrow at 10:00 AM in Conference Room B. Please update your Jira tickets with current estimations before the call.',
  },
  {
    label: '✈️ Flight Booking Receipt',
    model: 'naive_bayes',
    text: 'Dear Alex, your flight confirmation for booking #PNR78921 has been issued. Boarding begins at 2:30 PM at Terminal 3 Gate 12. Have a pleasant journey with us!',
  },
]

function formatDate(iso) {
  if (!iso) return '—'
  const d = new Date(iso)
  return d.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export default function ModelPerformance() {
  const [metricsData, setMetricsData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Controlled retraining state
  const [versionsData, setVersionsData] = useState(null)
  const [monitoringData, setMonitoringData] = useState(null)
  const [controlledRetraining, setControlledRetraining] = useState(false)
  const [retrainingResult, setRetrainingResult] = useState(null)
  const [showRetrainModal, setShowRetrainModal] = useState(false)

  // Live sandbox state
  const [inputText, setInputText] = useState(SAMPLE_PRESETS[0].text)
  const [selectedModel, setSelectedModel] = useState('logistic_regression')
  const [predicting, setPredicting] = useState(false)
  const [predictionResult, setPredictionResult] = useState(null)

  const fetchAllData = async () => {
    try {
      setLoading(true)
      setError(null)
      const [metricsRes, versionsRes, monitoringRes] = await Promise.all([
        modelsAPI.performance(),
        modelsAPI.versions(),
        modelsAPI.monitoring(),
      ])

      setMetricsData(metricsRes.data?.data || null)
      setVersionsData(versionsRes.data?.data || null)
      setMonitoringData(monitoringRes.data?.data || null)

      // Run sample classification
      handlePredict(SAMPLE_PRESETS[0].text, 'logistic_regression')
    } catch (err) {
      setError(err?.userMessage || 'Failed to load model performance data')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchAllData()
  }, [])

  const handleControlledRetrain = async () => {
    try {
      setControlledRetraining(true)
      setShowRetrainModal(false)
      const res = await modelsAPI.retrainControlled({
        acceptance_margin: 0.05,
        created_by: 'admin',
      })
      const result = res.data?.data
      setRetrainingResult(result)

      // Refresh metrics and versions
      const [metricsRes, versionsRes, monitoringRes] = await Promise.all([
        modelsAPI.performance(),
        modelsAPI.versions(),
        modelsAPI.monitoring(),
      ])
      setMetricsData(metricsRes.data?.data || null)
      setVersionsData(versionsRes.data?.data || null)
      setMonitoringData(monitoringRes.data?.data || null)
    } catch (err) {
      alert(err?.userMessage || 'Controlled retraining failed')
    } finally {
      setControlledRetraining(false)
    }
  }

  const handlePredict = async (textToPredict = inputText, modelToUse = selectedModel) => {
    if (!textToPredict.trim()) return
    try {
      setPredicting(true)
      const res = await modelsAPI.predict({
        text: textToPredict,
        model: modelToUse,
      })
      setPredictionResult(res.data?.data || null)
    } catch (err) {
      alert(err?.userMessage || 'Prediction failed')
    } finally {
      setPredicting(false)
    }
  }

  const lrMetrics = metricsData?.logistic_regression
  const nbMetrics = metricsData?.naive_bayes
  const datasetStats = metricsData?.dataset

  // Combine ROC points for chart
  const rocPoints = []
  if (lrMetrics?.roc_curve && nbMetrics?.roc_curve) {
    const len = Math.max(lrMetrics.roc_curve.length, nbMetrics.roc_curve.length)
    for (let i = 0; i < len; i++) {
      const lrPoint = lrMetrics.roc_curve[i] || lrMetrics.roc_curve[lrMetrics.roc_curve.length - 1]
      const nbPoint = nbMetrics.roc_curve[i] || nbMetrics.roc_curve[nbMetrics.roc_curve.length - 1]
      rocPoints.push({
        fpr: lrPoint.fpr,
        'Logistic Regression': lrPoint.tpr,
        'Naive Bayes': nbPoint.tpr,
        Baseline: lrPoint.fpr,
      })
    }
  }

  return (
    <div className="space-y-6">
      {/* Header bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
            <Brain className="w-6 h-6 text-brand-600 dark:text-brand-400" />
            Machine Learning Models &amp; Retraining Pipeline
          </h2>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Comparative evaluation, version control, and controlled retraining with verified user feedback
          </p>
        </div>
        <div className="flex items-center gap-2 self-start sm:self-auto">
          <button
            onClick={() => setShowRetrainModal(true)}
            disabled={controlledRetraining || loading}
            className="btn-primary flex items-center gap-2 text-sm shadow-sm"
          >
            <RefreshCw className={`w-4 h-4 ${controlledRetraining ? 'animate-spin' : ''}`} />
            {controlledRetraining ? 'Retraining Pipeline Running...' : 'Retrain with Feedback'}
          </button>
        </div>
      </div>

      {/* Retraining Result Banner */}
      {retrainingResult && (
        <div className={`p-4 rounded-xl border flex items-start gap-3 transition-all ${
          retrainingResult.promoted
            ? 'bg-emerald-50 dark:bg-emerald-950/30 border-emerald-200 dark:border-emerald-800 text-emerald-900 dark:text-emerald-200'
            : 'bg-amber-50 dark:bg-amber-950/30 border-amber-200 dark:border-amber-800 text-amber-900 dark:text-amber-200'
        }`}>
          {retrainingResult.promoted ? (
            <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
          ) : (
            <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
          )}
          <div className="flex-1 text-xs space-y-1">
            <p className="font-bold text-sm">
              {retrainingResult.promoted ? '✅ New Model Version Promoted!' : '⚠️ Model Retraining Evaluation Complete (Rejected)'}
            </p>
            <p>{retrainingResult.message}</p>
            <div className="flex flex-wrap gap-4 pt-1 font-mono text-[11px]">
              <span>Candidate Version: <strong>{retrainingResult.version}</strong></span>
              <span>LR Acc: <strong>{(retrainingResult.metrics?.logistic_regression?.accuracy * 100).toFixed(1)}%</strong></span>
              <span>NB Acc: <strong>{(retrainingResult.metrics?.naive_bayes?.accuracy * 100).toFixed(1)}%</strong></span>
              <span>Feedback Samples: <strong>{retrainingResult.metrics?.dataset?.feedback_samples_used ?? 0}</strong></span>
            </div>
          </div>
          <button
            onClick={() => setRetrainingResult(null)}
            className="p-1 text-slate-400 hover:text-slate-600"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {loading ? (
        <div className="card p-12 flex justify-center">
          <LoadingSpinner size="lg" message="Loading machine learning models and version audit log..." />
        </div>
      ) : error ? (
        <div className="card p-6 bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300">
          <p className="font-semibold">Error loading models</p>
          <p className="text-sm mt-1">{error}</p>
          <button onClick={fetchAllData} className="mt-3 btn-secondary text-xs">
            Retry
          </button>
        </div>
      ) : (
        <>
          {/* Phase 4: Model Versioning & Monitoring Overview Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="card p-4">
              <p className="text-xs text-slate-500 dark:text-slate-400 font-medium uppercase">Active Model Version</p>
              <div className="flex items-center gap-2 mt-1">
                <span className="text-2xl font-extrabold text-brand-600 dark:text-brand-400 font-mono">
                  {versionsData?.active_version || 'v1'}
                </span>
                <span className="text-[10px] font-bold bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300 px-2 py-0.5 rounded-full uppercase">
                  Production
                </span>
              </div>
              <p className="text-[11px] text-slate-400 mt-1">
                Last trained: {formatDate(metricsData?.trained_at)}
              </p>
            </div>

            <div className="card p-4">
              <p className="text-xs text-slate-500 dark:text-slate-400 font-medium uppercase">Approved Feedback</p>
              <p className="text-2xl font-bold text-slate-900 dark:text-white mt-1">
                {versionsData?.approved_feedback_count || 0}
              </p>
              <p className="text-[11px] text-slate-400 mt-1">
                Samples curated for retraining
              </p>
            </div>

            <div className="card p-4">
              <p className="text-xs text-slate-500 dark:text-slate-400 font-medium uppercase">Inter-Model Disagreement</p>
              <div className="flex items-baseline gap-2 mt-1">
                <p className="text-2xl font-bold text-purple-600 dark:text-purple-400">
                  {monitoringData?.disagreement_rate ?? 0}%
                </p>
                <span className="text-xs text-slate-400">
                  ({monitoringData?.disagreement_count ?? 0} emails)
                </span>
              </div>
              <p className="text-[11px] text-slate-400 mt-1">
                Live prediction divergences
              </p>
            </div>

            <div className="card p-4">
              <p className="text-xs text-slate-500 dark:text-slate-400 font-medium uppercase">User Correction Rate</p>
              <p className="text-2xl font-bold text-amber-600 dark:text-amber-400 mt-1">
                {monitoringData?.user_correction_rate ?? 0}%
              </p>
              <p className="text-[11px] text-slate-400 mt-1">
                Feedback override frequency
              </p>
            </div>
          </div>

          {/* Model Monitoring Alerts */}
          {monitoringData?.alerts && monitoringData.alerts.length > 0 && (
            <div className="space-y-2">
              {monitoringData.alerts.map((alt, idx) => (
                <div
                  key={idx}
                  className={`p-3 rounded-xl border flex items-center gap-3 text-xs ${
                    alt.type === 'warning'
                      ? 'bg-amber-50 dark:bg-amber-950/20 border-amber-200 dark:border-amber-800/40 text-amber-800 dark:text-amber-300'
                      : alt.type === 'healthy'
                      ? 'bg-emerald-50 dark:bg-emerald-950/20 border-emerald-200 dark:border-emerald-800/40 text-emerald-800 dark:text-emerald-300'
                      : 'bg-blue-50 dark:bg-blue-950/20 border-blue-200 dark:border-blue-800/40 text-blue-800 dark:text-blue-300'
                  }`}
                >
                  {alt.type === 'warning' ? (
                    <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
                  ) : alt.type === 'healthy' ? (
                    <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0" />
                  ) : (
                    <Activity className="w-4 h-4 text-blue-600 shrink-0" />
                  )}
                  <span className="font-medium">{alt.message}</span>
                </div>
              ))}
            </div>
          )}

          {/* Comparative Model Cards */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Logistic Regression Card */}
            {lrMetrics && (
              <div className="card p-5 space-y-4 border-t-4 border-t-brand-600">
                <div className="flex items-start justify-between">
                  <div>
                    <span className="text-[11px] font-bold text-brand-600 dark:text-brand-400 uppercase tracking-wider">
                      Linear Classifier
                    </span>
                    <h3 className="text-lg font-bold text-slate-900 dark:text-slate-100 mt-0.5">
                      Logistic Regression
                    </h3>
                  </div>
                  <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-brand-50 text-brand-700 dark:bg-brand-900/30 dark:text-brand-300">
                    L2 Regularized
                  </span>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-center">
                  <div className="p-2.5 rounded-lg bg-slate-50 dark:bg-navy-800/50">
                    <p className="text-[10px] text-slate-500 uppercase font-semibold">Accuracy</p>
                    <p className="text-base font-bold text-slate-800 dark:text-slate-100">
                      {(lrMetrics.accuracy * 100).toFixed(1)}%
                    </p>
                  </div>
                  <div className="p-2.5 rounded-lg bg-slate-50 dark:bg-navy-800/50">
                    <p className="text-[10px] text-slate-500 uppercase font-semibold">Precision</p>
                    <p className="text-base font-bold text-slate-800 dark:text-slate-100">
                      {(lrMetrics.precision * 100).toFixed(1)}%
                    </p>
                  </div>
                  <div className="p-2.5 rounded-lg bg-slate-50 dark:bg-navy-800/50">
                    <p className="text-[10px] text-slate-500 uppercase font-semibold">Recall</p>
                    <p className="text-base font-bold text-slate-800 dark:text-slate-100">
                      {(lrMetrics.recall * 100).toFixed(1)}%
                    </p>
                  </div>
                  <div className="p-2.5 rounded-lg bg-slate-50 dark:bg-navy-800/50">
                    <p className="text-[10px] text-slate-500 uppercase font-semibold">F1-Score</p>
                    <p className="text-base font-bold text-slate-800 dark:text-slate-100">
                      {(lrMetrics.f1 * 100).toFixed(1)}%
                    </p>
                  </div>
                </div>

                {/* Confusion Matrix */}
                {lrMetrics.confusion_matrix && (
                  <div>
                    <p className="text-xs font-semibold text-slate-700 dark:text-slate-300 mb-2">
                      Confusion Matrix (Test Split)
                    </p>
                    <div className="grid grid-cols-2 gap-2 text-center text-xs font-mono">
                      <div className="p-2.5 bg-emerald-50 dark:bg-emerald-950/20 border border-emerald-200 dark:border-emerald-800/40 rounded-lg">
                        <span className="text-[10px] text-emerald-600 block">True Negative (Ham)</span>
                        <span className="text-sm font-bold text-emerald-800 dark:text-emerald-200">
                          {lrMetrics.confusion_matrix.tn}
                        </span>
                      </div>
                      <div className="p-2.5 bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-800/40 rounded-lg">
                        <span className="text-[10px] text-red-600 block">False Positive (False Alarm)</span>
                        <span className="text-sm font-bold text-red-800 dark:text-red-200">
                          {lrMetrics.confusion_matrix.fp}
                        </span>
                      </div>
                      <div className="p-2.5 bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-800/40 rounded-lg">
                        <span className="text-[10px] text-red-600 block">False Negative (Missed Spam)</span>
                        <span className="text-sm font-bold text-red-800 dark:text-red-200">
                          {lrMetrics.confusion_matrix.fn}
                        </span>
                      </div>
                      <div className="p-2.5 bg-emerald-50 dark:bg-emerald-950/20 border border-emerald-200 dark:border-emerald-800/40 rounded-lg">
                        <span className="text-[10px] text-emerald-600 block">True Positive (Spam)</span>
                        <span className="text-sm font-bold text-emerald-800 dark:text-emerald-200">
                          {lrMetrics.confusion_matrix.tp}
                        </span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Multinomial Naive Bayes Card */}
            {nbMetrics && (
              <div className="card p-5 space-y-4 border-t-4 border-t-cyan-500">
                <div className="flex items-start justify-between">
                  <div>
                    <span className="text-[11px] font-bold text-cyan-600 dark:text-cyan-400 uppercase tracking-wider">
                      Probabilistic Classifier
                    </span>
                    <h3 className="text-lg font-bold text-slate-900 dark:text-slate-100 mt-0.5">
                      Multinomial Naive Bayes
                    </h3>
                  </div>
                  <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-cyan-50 text-cyan-700 dark:bg-cyan-900/30 dark:text-cyan-300">
                    Laplace α = 0.1
                  </span>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-center">
                  <div className="p-2.5 rounded-lg bg-slate-50 dark:bg-navy-800/50">
                    <p className="text-[10px] text-slate-500 uppercase font-semibold">Accuracy</p>
                    <p className="text-base font-bold text-slate-800 dark:text-slate-100">
                      {(nbMetrics.accuracy * 100).toFixed(1)}%
                    </p>
                  </div>
                  <div className="p-2.5 rounded-lg bg-slate-50 dark:bg-navy-800/50">
                    <p className="text-[10px] text-slate-500 uppercase font-semibold">Precision</p>
                    <p className="text-base font-bold text-slate-800 dark:text-slate-100">
                      {(nbMetrics.precision * 100).toFixed(1)}%
                    </p>
                  </div>
                  <div className="p-2.5 rounded-lg bg-slate-50 dark:bg-navy-800/50">
                    <p className="text-[10px] text-slate-500 uppercase font-semibold">Recall</p>
                    <p className="text-base font-bold text-slate-800 dark:text-slate-100">
                      {(nbMetrics.recall * 100).toFixed(1)}%
                    </p>
                  </div>
                  <div className="p-2.5 rounded-lg bg-slate-50 dark:bg-navy-800/50">
                    <p className="text-[10px] text-slate-500 uppercase font-semibold">F1-Score</p>
                    <p className="text-base font-bold text-slate-800 dark:text-slate-100">
                      {(nbMetrics.f1 * 100).toFixed(1)}%
                    </p>
                  </div>
                </div>

                {/* Confusion Matrix */}
                {nbMetrics.confusion_matrix && (
                  <div>
                    <p className="text-xs font-semibold text-slate-700 dark:text-slate-300 mb-2">
                      Confusion Matrix (Test Split)
                    </p>
                    <div className="grid grid-cols-2 gap-2 text-center text-xs font-mono">
                      <div className="p-2.5 bg-emerald-50 dark:bg-emerald-950/20 border border-emerald-200 dark:border-emerald-800/40 rounded-lg">
                        <span className="text-[10px] text-emerald-600 block">True Negative (Ham)</span>
                        <span className="text-sm font-bold text-emerald-800 dark:text-emerald-200">
                          {nbMetrics.confusion_matrix.tn}
                        </span>
                      </div>
                      <div className="p-2.5 bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-800/40 rounded-lg">
                        <span className="text-[10px] text-red-600 block">False Positive (False Alarm)</span>
                        <span className="text-sm font-bold text-red-800 dark:text-red-200">
                          {nbMetrics.confusion_matrix.fp}
                        </span>
                      </div>
                      <div className="p-2.5 bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-800/40 rounded-lg">
                        <span className="text-[10px] text-red-600 block">False Negative (Missed Spam)</span>
                        <span className="text-sm font-bold text-red-800 dark:text-red-200">
                          {nbMetrics.confusion_matrix.fn}
                        </span>
                      </div>
                      <div className="p-2.5 bg-emerald-50 dark:bg-emerald-950/20 border border-emerald-200 dark:border-emerald-800/40 rounded-lg">
                        <span className="text-[10px] text-emerald-600 block">True Positive (Spam)</span>
                        <span className="text-sm font-bold text-emerald-800 dark:text-emerald-200">
                          {nbMetrics.confusion_matrix.tp}
                        </span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Version Audit Log Table */}
          <div className="card p-5 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-semibold text-slate-800 dark:text-slate-200 text-sm flex items-center gap-2">
                  <History className="w-4 h-4 text-brand-600 dark:text-brand-400" />
                  Model Retraining History &amp; Version Audit Log
                </h3>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                  Audit trail of all controlled retraining runs, feedback samples incorporated, and promotion decisions
                </p>
              </div>
            </div>

            {(!versionsData?.history || versionsData.history.length === 0) ? (
              <div className="py-6 text-center text-xs text-slate-400">
                No past retraining runs recorded yet. Current active version is <strong>v1</strong>.
              </div>
            ) : (
              <div className="overflow-x-auto rounded-xl border border-slate-100 dark:border-navy-700">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Version</th>
                      <th>Trained At</th>
                      <th>Dataset Samples</th>
                      <th>Feedback Incorporated</th>
                      <th>Status</th>
                      <th>Audit Notes</th>
                    </tr>
                  </thead>
                  <tbody>
                    {versionsData.history.map((item) => (
                      <tr key={item.id} className="font-mono text-xs">
                        <td>
                          <span className="font-bold text-brand-600 dark:text-brand-400">
                            {item.version}
                          </span>
                        </td>
                        <td>{formatDate(item.trained_at)}</td>
                        <td>{item.dataset_size}</td>
                        <td>{item.feedback_samples} samples</td>
                        <td>
                          <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase ${
                            item.status === 'promoted'
                              ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300'
                              : 'bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-300'
                          }`}>
                            {item.status}
                          </span>
                        </td>
                        <td className="font-sans text-slate-600 dark:text-slate-400 max-w-xs truncate">
                          {item.notes || '—'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Interactive Live Testing Sandbox */}
          <div className="card p-6 space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
                  <FlaskConical className="w-5 h-5 text-brand-600 dark:text-brand-400" />
                  Live Model Testing Sandbox
                </h3>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                  Test custom messages against active models to inspect explainability weights and classification confidence
                </p>
              </div>

              {/* Model Selector Tabs */}
              <div className="flex items-center gap-1 bg-slate-100 dark:bg-navy-800 p-1 rounded-xl self-start sm:self-auto">
                <button
                  type="button"
                  onClick={() => setSelectedModel('logistic_regression')}
                  className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-all ${
                    selectedModel === 'logistic_regression'
                      ? 'bg-white dark:bg-navy-900 text-brand-600 dark:text-brand-400 shadow-sm'
                      : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
                  }`}
                >
                  Logistic Regression
                </button>
                <button
                  type="button"
                  onClick={() => setSelectedModel('naive_bayes')}
                  className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-all ${
                    selectedModel === 'naive_bayes'
                      ? 'bg-white dark:bg-navy-900 text-cyan-600 dark:text-cyan-400 shadow-sm'
                      : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
                  }`}
                >
                  Naive Bayes
                </button>
              </div>
            </div>

            {/* Presets */}
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs text-slate-500 font-medium">Quick Presets:</span>
              {SAMPLE_PRESETS.map((preset, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => {
                    setInputText(preset.text)
                    setSelectedModel(preset.model)
                    handlePredict(preset.text, preset.model)
                  }}
                  className="px-2.5 py-1 text-xs rounded-lg border border-slate-200 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors font-medium text-slate-700 dark:text-slate-300"
                >
                  {preset.label}
                </button>
              ))}
            </div>

            {/* Email Input Textarea */}
            <div className="space-y-2">
              <textarea
                id="email-sandbox-input"
                rows={4}
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                placeholder="Paste any email text, subject, or message here to test real-time classification..."
                className="input w-full p-3 text-xs font-mono leading-relaxed resize-y"
              />
              <div className="flex justify-end">
                <button
                  id="classify-btn"
                  onClick={() => handlePredict()}
                  disabled={predicting || !inputText.trim()}
                  className="btn-primary text-xs flex items-center gap-1.5"
                >
                  <Send className={`w-3.5 h-3.5 ${predicting ? 'animate-pulse' : ''}`} />
                  {predicting ? 'Analyzing Message...' : 'Classify Message'}
                </button>
              </div>
            </div>

            {/* Classification Result Display */}
            {predictionResult && (
              <div
                className={`p-4 rounded-xl border transition-all ${
                  predictionResult.is_spam
                    ? 'bg-red-50/70 dark:bg-red-950/20 border-red-200 dark:border-red-900/40 text-red-900 dark:text-red-200'
                    : 'bg-emerald-50/70 dark:bg-emerald-950/20 border-emerald-200 dark:border-emerald-900/40 text-emerald-900 dark:text-emerald-200'
                }`}
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div className="flex items-center gap-3">
                    <span
                      className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider ${
                        predictionResult.is_spam
                          ? 'bg-red-600 text-white shadow-sm shadow-red-500/50'
                          : 'bg-emerald-600 text-white shadow-sm shadow-emerald-500/50'
                      }`}
                    >
                      {predictionResult.is_spam ? '🚨 SPAM DETECTED' : '✅ SAFE (HAM)'}
                    </span>
                    <span className="text-xs text-slate-600 dark:text-slate-300 font-medium">
                      Model: <strong>{predictionResult.model_used}</strong>
                    </span>
                  </div>
                  <div className="text-right">
                    <span className="text-xs font-semibold">Confidence: </span>
                    <span className="text-sm font-extrabold">
                      {(predictionResult.confidence * 100).toFixed(1)}%
                    </span>
                  </div>
                </div>

                {/* Probability meters */}
                <div className="mt-3 space-y-1.5">
                  <div className="flex justify-between text-[11px] font-semibold text-slate-600 dark:text-slate-400">
                    <span>Safe Probability: {(predictionResult.ham_probability * 100).toFixed(1)}%</span>
                    <span>Spam Probability: {(predictionResult.spam_probability * 100).toFixed(1)}%</span>
                  </div>
                  <div className="w-full bg-slate-200 dark:bg-navy-700 h-2.5 rounded-full overflow-hidden flex">
                    <div
                      className="bg-emerald-500 h-full transition-all duration-500"
                      style={{ width: `${predictionResult.ham_probability * 100}%` }}
                    />
                    <div
                      className="bg-red-500 h-full transition-all duration-500"
                      style={{ width: `${predictionResult.spam_probability * 100}%` }}
                    />
                  </div>
                </div>

                {/* Explainability keyword tokens */}
                {predictionResult.top_signals && predictionResult.top_signals.length > 0 && (
                  <div className="mt-4 pt-3 border-t border-slate-200/60 dark:border-navy-600/40">
                    <p className="text-[11px] font-semibold text-slate-700 dark:text-slate-300 mb-2">
                      Key Discriminative Features (Explainable AI Signal Tokens):
                    </p>
                    <div className="flex flex-wrap gap-1.5">
                      {predictionResult.top_signals.map((sig, idx) => (
                        <span
                          key={idx}
                          className={`text-[10px] px-2 py-0.5 rounded-md font-mono font-medium flex items-center gap-1 ${
                            sig.score > 0
                              ? 'bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-300'
                              : 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300'
                          }`}
                        >
                          {sig.word}
                          <span className="opacity-75 text-[9px] font-normal">
                            ({sig.score > 0 ? '+' : ''}{sig.score.toFixed(2)})
                          </span>
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </>
      )}

      {/* Retraining Confirmation Modal */}
      {showRetrainModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fade-in">
          <div className="card w-full max-w-md p-6 space-y-4 shadow-2xl border border-slate-200 dark:border-navy-700">
            <div className="flex items-start gap-3">
              <div className="w-10 h-10 rounded-xl bg-purple-50 dark:bg-purple-900/20 flex items-center justify-center shrink-0">
                <Brain className="w-5 h-5 text-purple-600 dark:text-purple-400" />
              </div>
              <div>
                <h3 className="font-bold text-slate-900 dark:text-white text-base">
                  Confirm Controlled Retraining
                </h3>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                  Start the ML retraining pipeline with verified user feedback records?
                </p>
              </div>
            </div>

            <div className="p-3 bg-slate-50 dark:bg-navy-800/50 rounded-xl text-xs space-y-1.5 text-slate-600 dark:text-slate-300">
              <div className="flex justify-between">
                <span>Approved Feedback Samples:</span>
                <span className="font-bold text-emerald-600">{versionsData?.approved_feedback_count || 0}</span>
              </div>
              <div className="flex justify-between">
                <span>Current Production Version:</span>
                <span className="font-bold font-mono">{versionsData?.active_version || 'v1'}</span>
              </div>
              <div className="flex justify-between">
                <span>Acceptance Policy:</span>
                <span className="font-medium text-slate-800 dark:text-slate-200">Strict Validation (≥85% Acc)</span>
              </div>
            </div>

            <p className="text-[11px] text-slate-400 leading-relaxed">
              Candidate models will be trained on the combined dataset and evaluated on a held-out test split. If candidate models meet or exceed the validation criteria, they will be promoted to the next version automatically. Otherwise, production models will remain unchanged.
            </p>

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setShowRetrainModal(false)}
                className="btn-secondary text-xs px-4 py-2"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleControlledRetrain}
                className="btn-primary text-xs px-4 py-2 flex items-center gap-1.5"
              >
                <Check className="w-4 h-4" />
                Proceed with Retraining
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
