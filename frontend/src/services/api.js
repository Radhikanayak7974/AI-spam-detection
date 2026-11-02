/**
 * Centralized Axios instance for all backend API calls.
 * All routes proxy through Vite to http://localhost:5000
 */
import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 120000,  // 2 minutes – sync can take time
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
})

// ── Request interceptor ────────────────────────────────────────
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('spamguard_token') || sessionStorage.getItem('spamguard_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// ── Response interceptor ───────────────────────────────────────
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // If 401 Unauthorized from an authenticated endpoint, notify
    if (error.response?.status === 401) {
      // Clear token if expired or invalid
      if (window.location.pathname.startsWith('/overview') ||
          window.location.pathname.startsWith('/inbox') ||
          window.location.pathname.startsWith('/spam') ||
          window.location.pathname.startsWith('/safe')) {
        localStorage.removeItem('spamguard_token')
        sessionStorage.removeItem('spamguard_token')
      }
    }
    const message =
      error.response?.data?.message ||
      error.message ||
      'An unexpected error occurred'
    return Promise.reject({ ...error, userMessage: message })
  }
)

// ── API methods ───────────────────────────────────────────────

export const healthAPI = {
  check: () => api.get('/health'),
}

// ── SpamGuard User Account Authentication ─────────────────────
export const userAuthAPI = {
  register: (data) => api.post('/auth/register', data),
  login:    (data) => api.post('/auth/user/login', data),
  logout:   ()     => api.post('/auth/user/logout'),
  me:       ()     => api.get('/auth/user/me'),
}

// ── Google Gmail OAuth Connection (Separate system) ───────────
export const authAPI = {
  status:  () => api.get('/auth/status'),
  login:   () => api.get('/auth/login'),
  logout:  () => api.post('/auth/logout'),
}

export const dashboardAPI = {
  stats:          () => api.get('/dashboard/stats'),
  recentActivity: () => api.get('/dashboard/recent-activity'),
}

export const emailsAPI = {
  list:   (params = {}) => api.get('/emails',      { params }),
  spam:   (params = {}) => api.get('/emails/spam', { params }),
  safe:   (params = {}) => api.get('/emails/safe', { params }),
  detail: (id)          => api.get(`/emails/${id}`),
}

export const modelsAPI = {
  performance:       ()          => api.get('/models/performance'),
  predict:           (data)      => api.post('/models/predict', data),
  train:             ()          => api.post('/models/train'),
  retrainControlled: (data = {}) => api.post('/models/retrain', data),
  versions:          ()          => api.get('/models/versions'),
  monitoring:        ()          => api.get('/models/monitoring'),
}

// ── Phase 3: Gmail Sync API ────────────────────────────────────
export const gmailAPI = {
  sync:       (opts = {}) => api.post('/gmail/sync', opts),
  syncStart:  ()          => api.post('/gmail/sync/start'),
  syncStop:   ()          => api.post('/gmail/sync/stop'),
  syncStatus: ()          => api.get('/gmail/sync-status'),
  messages:   (params={}) => api.get('/gmail/messages', { params }),
}

// ── Phase 3: Settings API ──────────────────────────────────────
export const settingsAPI = {
  getSyncSettings:    ()     => api.get('/settings/sync'),
  updateSyncSettings: (data) => api.put('/settings/sync', data),
}

// ── Phase 4: Feedback API ──────────────────────────────────────
export const feedbackAPI = {
  submit: (data)        => api.post('/feedback', data),
  list:   (params = {}) => api.get('/feedback', { params }),
  stats:  ()            => api.get('/feedback/stats'),
  update: (id, data)    => api.patch(`/feedback/${id}`, data),
  delete: (id)          => api.delete(`/feedback/${id}`),
}

// ── Phase 4: Analytics API ─────────────────────────────────────
export const analyticsAPI = {
  overview:        (params = {}) => api.get('/analytics/overview', { params }),
  trends:          (params = {}) => api.get('/analytics/trends', { params }),
  senders:         (params = {}) => api.get('/analytics/senders', { params }),
  patterns:        ()            => api.get('/analytics/patterns'),
  modelComparison: ()            => api.get('/analytics/model-comparison'),
}

export default api

