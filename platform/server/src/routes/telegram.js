import { Router } from 'express'
import { supabase } from '../middleware/auth.js'

export const telegramRoutes = Router()

// POST /api/telegram/verify — verify 6-digit code from /start
// The Python runtime generates codes and stores them in telegram_users table
telegramRoutes.post('/verify', async (req, res, next) => {
  try {
    const { code } = req.body

    // Lookup the pending verification in telegram_users (code set by Python bot on /start)
    const { data: pending, error: lookupErr } = await supabase
      .from('telegram_users')
      .select('user_id, telegram_user_id')
      .eq('verification_code', code)
      .eq('verified', false)
      .gte('code_expires_at', new Date().toISOString())
      .single()

    if (lookupErr || !pending) {
      return res.status(400).json({ error: 'Invalid or expired code. Send /start to @JunctionAIBot to get a new code.' })
    }

    // Link: update the row to associate with this Junction user and mark verified
    const { error: linkErr } = await supabase
      .from('telegram_users')
      .update({
        user_id: req.userId,
        verified: true,
        verification_code: null,
        code_expires_at: null,
      })
      .eq('telegram_user_id', pending.telegram_user_id)

    if (linkErr) throw linkErr

    res.json({ verified: true, telegram_user_id: pending.telegram_user_id })
  } catch (err) { next(err) }
})

// GET /api/telegram/status — check if user has linked Telegram
telegramRoutes.get('/status', async (req, res, next) => {
  try {
    const { data, error } = await supabase
      .from('telegram_users')
      .select('telegram_user_id, verified, created_at')
      .eq('user_id', req.userId)
      .single()

    if (error && error.code !== 'PGRST116') throw error
    res.json(data || { verified: false })
  } catch (err) { next(err) }
})

// GET /api/telegram/channels — list user's linked agent channels
telegramRoutes.get('/channels', async (req, res, next) => {
  try {
    const { data, error } = await supabase
      .from('agent_channels')
      .select('*, agents(display_name, slug)')
      .eq('user_id', req.userId)
      .order('created_at', { ascending: false })

    if (error) throw error
    res.json(data || [])
  } catch (err) { next(err) }
})

// DELETE /api/telegram/channels/:id — unlink a channel
telegramRoutes.delete('/channels/:id', async (req, res, next) => {
  try {
    const { error } = await supabase
      .from('agent_channels')
      .delete()
      .eq('id', req.params.id)
      .eq('user_id', req.userId)

    if (error) throw error
    res.json({ deleted: true })
  } catch (err) { next(err) }
})
