// Check if user has exceeded monthly spend limit
export async function checkBillingLimit(userId, supabase) {
  // Get start of current month in ISO format
  const startOfMonth = new Date(new Date().getFullYear(), new Date().getMonth(), 1).toISOString()

  // Sum cost_usd for this user this month from usage_log
  const { data, error } = await supabase
    .from('usage_log')
    .select('cost_usd')
    .eq('user_id', userId)
    .gte('created_at', startOfMonth)

  if (error) {
    console.warn('Billing check failed, allowing request:', error.message)
    return // fail open — don't block user on billing DB failure
  }

  const totalSpent = (data || []).reduce((sum, row) => sum + (row.cost_usd || 0), 0)
  const FREE_PLAN_LIMIT_USD = 5.00

  if (totalSpent >= FREE_PLAN_LIMIT_USD) {
    const err = new Error('Monthly spend limit reached. Upgrade to continue.')
    err.status = 429
    throw err
  }
}

// Check if user has hit agent count limit
export async function checkAgentLimit(userId, supabase) {
  const { count, error } = await supabase
    .from('agents')
    .select('id', { count: 'exact', head: true })
    .eq('user_id', userId)

  if (error) {
    console.warn('Agent limit check failed, allowing request:', error.message)
    return // fail open
  }

  const FREE_PLAN_AGENT_LIMIT = 3

  if (count >= FREE_PLAN_AGENT_LIMIT) {
    const err = new Error('Agent limit reached (3 agents on free plan). Upgrade to create more.')
    err.status = 429
    throw err
  }
}
