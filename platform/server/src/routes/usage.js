import { Router } from 'express'
import { supabase } from '../middleware/auth.js'

export const usageRoutes = Router()

// GET /api/usage — monthly usage summary
usageRoutes.get('/', async (req, res, next) => {
  try {
    const now = new Date()
    const startOfMonth = new Date(now.getFullYear(), now.getMonth(), 1).toISOString()

    const { data, error } = await supabase
      .from('usage_log')
      .select('provider, model, input_tokens, output_tokens, cost_usd')
      .eq('user_id', req.userId)
      .gte('created_at', startOfMonth)

    if (error) throw error

    const summary = {
      total_input_tokens: 0,
      total_output_tokens: 0,
      total_cost_usd: 0,
      by_model: {},
      message_count: 0,
    }

    for (const row of (data || [])) {
      summary.total_input_tokens += row.input_tokens
      summary.total_output_tokens += row.output_tokens
      summary.total_cost_usd += parseFloat(row.cost_usd)
      summary.message_count++

      if (!summary.by_model[row.model]) {
        summary.by_model[row.model] = { input_tokens: 0, output_tokens: 0, cost_usd: 0, count: 0 }
      }
      summary.by_model[row.model].input_tokens += row.input_tokens
      summary.by_model[row.model].output_tokens += row.output_tokens
      summary.by_model[row.model].cost_usd += parseFloat(row.cost_usd)
      summary.by_model[row.model].count++
    }

    summary.total_cost_usd = Math.round(summary.total_cost_usd * 1000000) / 1000000

    res.json(summary)
  } catch (err) { next(err) }
})

// GET /api/usage/agents — per-agent breakdown for current month
usageRoutes.get('/agents', async (req, res, next) => {
  try {
    const now = new Date()
    const startOfMonth = new Date(now.getFullYear(), now.getMonth(), 1).toISOString()

    const { data, error } = await supabase
      .from('usage_log')
      .select('agent_id, input_tokens, output_tokens, cost_usd, agents(display_name)')
      .eq('user_id', req.userId)
      .gte('created_at', startOfMonth)

    if (error) throw error

    const byAgent = {}
    for (const row of (data || [])) {
      const id = row.agent_id || 'system'
      if (!byAgent[id]) {
        byAgent[id] = {
          agent_id: row.agent_id,
          display_name: row.agents?.display_name || 'System',
          input_tokens: 0,
          output_tokens: 0,
          cost_usd: 0,
          message_count: 0,
        }
      }
      byAgent[id].input_tokens += row.input_tokens
      byAgent[id].output_tokens += row.output_tokens
      byAgent[id].cost_usd += parseFloat(row.cost_usd)
      byAgent[id].message_count++
    }

    const agents = Object.values(byAgent)
      .map(a => ({ ...a, cost_usd: Math.round(a.cost_usd * 1000000) / 1000000 }))
      .sort((a, b) => b.cost_usd - a.cost_usd)

    res.json(agents)
  } catch (err) { next(err) }
})
