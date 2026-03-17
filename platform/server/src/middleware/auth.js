import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  process.env.SUPABASE_URL || '',
  process.env.SUPABASE_SERVICE_KEY || ''  // Service key for server-side operations
)

export { supabase }

/**
 * Auth middleware: verifies the Supabase JWT from Authorization header.
 * Attaches req.userId (UUID) for downstream routes.
 */
export async function authMiddleware(req, res, next) {
  const token = req.headers.authorization?.replace('Bearer ', '')
  if (!token) {
    return res.status(401).json({ error: 'Missing authorization token' })
  }

  try {
    const { data: { user }, error } = await supabase.auth.getUser(token)
    if (error || !user) {
      return res.status(401).json({ error: 'Invalid token' })
    }
    req.userId = user.id
    next()
  } catch (err) {
    return res.status(401).json({ error: 'Authentication failed' })
  }
}
