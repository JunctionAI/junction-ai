import { randomUUID } from 'crypto'

export function loggingMiddleware(req, res, next) {
  req.requestId = randomUUID()
  res.set('X-Request-ID', req.requestId)
  const start = Date.now()

  res.on('finish', () => {
    const duration = Date.now() - start
    const entry = {
      timestamp: new Date().toISOString(),
      request_id: req.requestId,
      method: req.method,
      path: req.path,
      status: res.statusCode,
      duration_ms: duration,
      user_id: req.userId || null,
    }
    console.log(JSON.stringify(entry))
    if (duration > 10000) {
      console.warn(JSON.stringify({ ...entry, type: 'slow_request' }))
    }
  })

  next()
}
