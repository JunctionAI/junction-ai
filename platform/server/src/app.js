import express from 'express'
import cors from 'cors'
import helmet from 'helmet'
import rateLimit from 'express-rate-limit'
import { authMiddleware } from './middleware/auth.js'
import { profileRoutes } from './routes/profile.js'
import { agentRoutes } from './routes/agents.js'
import { telegramRoutes } from './routes/telegram.js'
import { usageRoutes } from './routes/usage.js'
import { tidefixRoutes } from './routes/tidefix.js'
import { companionRoutes } from './routes/companions.js'
import { loggingMiddleware } from './middleware/logging.js'

const app = express()
const PORT = process.env.PORT || 3001

// ─── Structured request logging ──────────────────────────────────────────────
app.use(loggingMiddleware)

// ─── Security headers ────────────────────────────────────────────────────────
app.use(helmet())

// ─── CORS — only allow our own frontend ─────────────────────────────────────
const ALLOWED_ORIGINS = [
  'https://app.getjunction.ai',
  'http://localhost:5173',
  'null',  // file:// protocol sends 'null' as origin
]
app.use(cors({
  origin: (origin, cb) => {
    // Allow server-to-server requests (no origin), listed origins, and file:// (null)
    if (!origin || ALLOWED_ORIGINS.includes(origin) || origin === 'null') return cb(null, true)
    cb(new Error('Not allowed by CORS'))
  },
  credentials: true,
}))

// ─── Body parsing with size limits ───────────────────────────────────────────
app.use(express.json({ limit: '50kb' }))

// ─── Rate limiting ───────────────────────────────────────────────────────────
// General API: 100 requests per minute per IP
const generalLimiter = rateLimit({
  windowMs: 60 * 1000,
  max: 100,
  standardHeaders: true,
  legacyHeaders: false,
  message: { error: 'Too many requests. Please slow down.' },
})

// Expensive AI endpoints: 20 per minute per IP
const aiLimiter = rateLimit({
  windowMs: 60 * 1000,
  max: 20,
  standardHeaders: true,
  legacyHeaders: false,
  message: { error: 'Too many AI requests. Please wait a moment.' },
})

// Voice uploads: 10 per minute per IP
const voiceLimiter = rateLimit({
  windowMs: 60 * 1000,
  max: 10,
  standardHeaders: true,
  legacyHeaders: false,
  message: { error: 'Too many voice uploads. Please wait.' },
})

app.use('/api/', generalLimiter)
app.use('/api/profile/compile', aiLimiter)
app.use('/api/profile/voice', voiceLimiter)
app.use('/api/agents/preview-first-message', aiLimiter)
app.use('/api/agents/:id/test', aiLimiter)

// ─── Health check ─────────────────────────────────────────────────────────────
app.get('/api/health', (req, res) => res.json({ status: 'ok' }))

// ─── Protected routes ─────────────────────────────────────────────────────────
app.use('/api/profile', authMiddleware, profileRoutes)
app.use('/api/agents', authMiddleware, agentRoutes)
app.use('/api/telegram', authMiddleware, telegramRoutes)
app.use('/api/usage', authMiddleware, usageRoutes)
app.use('/api/tidefix', tidefixRoutes)  // No auth — local-only data, read from bot files
app.use('/api/companions', companionRoutes)  // No auth — local-only recovery companion data

// ─── Error handler — never leak internals ────────────────────────────────────
app.use((err, req, res, _next) => {
  // CORS errors
  if (err.message === 'Not allowed by CORS') {
    return res.status(403).json({ error: 'Forbidden' })
  }

  const status = err.status || 500
  console.error(JSON.stringify({
    timestamp: new Date().toISOString(),
    request_id: req.requestId || null,
    error: err.message,
    status,
    user_id: req.userId || null,
  }))

  // Never send stack traces or internal messages to clients
  res.status(status).json({ error: err.message || 'Internal server error' })
})

app.listen(PORT, () => {
  console.log(`Junction AI API running on port ${PORT}`)
})
