import { Router } from 'express'
import { supabase } from '../middleware/auth.js'
import Anthropic from '@anthropic-ai/sdk'
import { validateAgentInput, validateMessage } from '../middleware/validate.js'
import { addMemory, getUserMemoryProfile } from '../services/memory.js'
import { checkBillingLimit, checkAgentLimit } from '../middleware/billing.js'

export const agentRoutes = Router()

// GET /api/agents
agentRoutes.get('/', async (req, res, next) => {
  try {
    const { data, error } = await supabase
      .from('agents')
      .select('*')
      .eq('user_id', req.userId)
      .order('created_at', { ascending: false })

    if (error) throw error
    res.json(data || [])
  } catch (err) { next(err) }
})

// POST /api/agents/preview-first-message — generate preview intro WITHOUT creating agent
// MUST be before /:id routes so Express doesn't treat 'preview-first-message' as an agent ID
agentRoutes.post('/preview-first-message', async (req, res, next) => {
  try {
    const { display_name, goal_domain, dream_outcome, inspirations, expertise, personality, accountability_level, check_in_style } = validateAgentInput(req.body)

    const { data: profile } = await supabase
      .from('user_profiles')
      .select('profile_text')
      .eq('user_id', req.userId)
      .single()

    const accountabilityDesc = (accountability_level || 50) >= 61
      ? 'direct and uncompromising — you call out patterns and excuses with care but without softening'
      : (accountability_level || 50) >= 31
      ? 'balanced — you encourage and challenge in equal measure'
      : 'warm and encouraging — you celebrate progress and ask questions rather than push'

    await checkBillingLimit(req.userId, supabase)

    const client = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY })

    const claudePromise = client.messages.create({
      model: 'claude-opus-4-6',
      max_tokens: 1000,
      messages: [{
        role: 'user',
        content: `You are ${display_name || 'an AI agent'}, a ${personality || 'coaching'}-style agent focused on ${goal_domain || 'personal development'}.

User profile:
${profile?.profile_text || 'No profile yet.'}

The user's dream outcome: "${dream_outcome}"
${inspirations ? `Inspirations they've cited: ${inspirations}` : ''}
${expertise ? `Your areas of expertise: ${expertise}` : ''}
Your accountability style: ${accountabilityDesc}

Write your first message to this person. This is your introduction.

Rules:
- Reference their dream outcome ("${dream_outcome}") by name — show you know what they're working toward
- Establish who you are and how you'll work together
- Set the tone for your relationship (${personality} style)
- Briefly explain how you'll check in (${check_in_style?.replace(/_/g, ' ') || 'daily check-ins'})
- End with one specific, direct question that gets them thinking immediately
- Keep it to 3-4 short paragraphs. Mobile-readable. No bullet points in the intro.
- Write in first person as the agent, directly to the user`
      }],
    })

    const timeoutPromise = new Promise((_, reject) =>
      setTimeout(() => reject(Object.assign(new Error('AI service timeout. Please try again.'), { status: 503 })), 30000)
    )

    const response = await Promise.race([claudePromise, timeoutPromise])

    const firstMessage = response.content[0].text

    await supabase.from('usage_log').insert({
      user_id: req.userId,
      provider: 'anthropic',
      model: 'claude-opus-4-6',
      input_tokens: response.usage?.input_tokens || 0,
      output_tokens: response.usage?.output_tokens || 0,
      cost_usd: ((response.usage?.input_tokens || 0) * 0.000015 + (response.usage?.output_tokens || 0) * 0.000075),
    })

    res.json({ first_message: firstMessage })
  } catch (err) { next(err) }
})

// POST /api/agents — create agent (generates AGENT.md via Opus 4.6)
agentRoutes.post('/', async (req, res, next) => {
  try {
    const {
      display_name, purpose, personality, knowledge,
      goal_domain, dream_outcome, inspirations, expertise,
      accountability_level, check_in_frequency, check_in_style,
    } = validateAgentInput(req.body)
    const schedule = req.body.schedule || undefined

    const { data: profile } = await supabase
      .from('user_profiles')
      .select('profile_text')
      .eq('user_id', req.userId)
      .single()

    const accountabilityLevel = accountability_level || 50
    const accountabilityProtocol = accountabilityLevel >= 61
      ? `You hold the user to a high standard. When you detect excuses, avoidance, or rationalisation, you name it directly and kindly. You do not let them off the hook. You ask the hard question. You care too much about their outcome to let comfort get in the way.`
      : accountabilityLevel >= 31
      ? `You balance encouragement with challenge. You celebrate genuine wins and probe gently when something feels off. You ask what's really going on when progress stalls.`
      : `You lead with warmth and curiosity. You celebrate every step forward. You ask questions rather than push. You create a safe space for honesty.`

    await checkBillingLimit(req.userId, supabase)
    await checkAgentLimit(req.userId, supabase)

    const client = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY })

    const claudePromise = client.messages.create({
      model: 'claude-opus-4-6',
      max_tokens: 3000,
      messages: [{
        role: 'user',
        content: `Generate a complete AGENT.md identity file for a personal AI agent.

Agent Name: ${display_name}
Domain: ${goal_domain || 'General'}
Dream Outcome for User: ${dream_outcome || purpose}
Personality Style: ${personality}
Inspirations/Influences: ${inspirations || 'Not specified'}
Areas of Expertise: ${expertise || 'Not specified'}
Accountability Level: ${accountabilityLevel}/100
Check-in Style: ${check_in_style?.replace(/_/g, ' ') || 'daily check-in'}
Check-in Frequency: ${check_in_frequency || 'daily'}

User Context:
${profile?.profile_text || 'No profile compiled yet.'}

Generate a complete AGENT.md following this exact structure:

# AGENT.md — ${display_name}

### IDENTITY
2-3 paragraphs. Who is this agent? What is their role in the user's life? Ground their personality and expertise in the stated inspirations (${inspirations || 'none stated'}) — if specific people or books are mentioned, let their philosophy shape how this agent thinks and communicates. Make this feel like a specific person, not a generic assistant.

### EXPERTISE
What this agent knows deeply. Based on: ${expertise || domain}. Be specific. List the mental models, frameworks, and knowledge domains they draw on.

### MISSION
One sentence: what this agent exists to do. Reference the dream outcome: "${dream_outcome || purpose}" by name.

### PERSONALITY
Bullet points on tone, communication style, and character. Shaped by ${personality} archetype and the stated inspirations.

### ACCOUNTABILITY PROTOCOL
${accountabilityProtocol}

Write 3-4 bullet points describing exactly how this agent holds the user accountable in practice.

### SESSION STARTUP
1. Read this file (AGENT.md)
2. Load user profile
3. Review recent conversation history
4. Check-in style for scheduled messages: ${check_in_style?.replace(/_/g, ' ') || 'brief daily check-in'}
5. Now respond

### SYSTEM CAPABILITIES
You can emit structured markers in responses:
- [STATE UPDATE: key information to remember about this user]
- [EVENT: type|SEVERITY|payload]

### OUTPUT FORMAT RULES
- Short paragraphs for mobile readability
- No markdown tables
- Bold key points with **asterisks**
- Conversational but purposeful

### STANDING ORDERS
Operational rules specific to this agent's mission. At least 5 specific rules tied directly to the dream outcome: "${dream_outcome || purpose}". These should feel like instructions written by the world's best coach for this specific person working toward this specific goal.

Make this feel alive. Not a template — a real agent identity.`
      }],
    })

    const timeoutPromise = new Promise((_, reject) =>
      setTimeout(() => reject(Object.assign(new Error('AI service timeout. Please try again.'), { status: 503 })), 30000)
    )

    const response = await Promise.race([claudePromise, timeoutPromise])

    const agentMd = response.content[0].text
    const slug = display_name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '')

    const { data: agent, error } = await supabase
      .from('agents')
      .insert({
        user_id: req.userId,
        slug,
        display_name,
        purpose: dream_outcome || purpose,
        agent_md: agentMd,
        knowledge_md: knowledge || '',
        context_md: `# CONTEXT.md — ${display_name}\n## Last Updated: ${new Date().toISOString().split('T')[0]}\n\n### Current Status\nNewly created. Awaiting first interaction.\n\n### Active Priorities\n(None yet)\n`,
      })
      .select()
      .single()

    if (error) throw error

    if (knowledge) {
      await supabase.from('agent_files').insert({
        agent_id: agent.id,
        file_type: 'skill',
        filename: 'initial-knowledge.md',
        content: knowledge,
      })
    }

    if (schedule) {
      await supabase.from('agent_schedules').insert({
        agent_id: agent.id,
        task_name: 'scheduled_task',
        cron_expression: schedule.cron_expression,
        task_prompt: schedule.task_prompt,
        description: schedule.description,
      })
    }

    await supabase.from('usage_log').insert({
      user_id: req.userId,
      agent_id: agent.id,
      provider: 'anthropic',
      model: 'claude-opus-4-6',
      input_tokens: response.usage?.input_tokens || 0,
      output_tokens: response.usage?.output_tokens || 0,
      cost_usd: ((response.usage?.input_tokens || 0) * 0.000015 + (response.usage?.output_tokens || 0) * 0.000075),
    })

    res.status(201).json(agent)
  } catch (err) { next(err) }
})

// GET /api/agents/:id
agentRoutes.get('/:id', async (req, res, next) => {
  try {
    const { data, error } = await supabase
      .from('agents')
      .select('*')
      .eq('id', req.params.id)
      .eq('user_id', req.userId)
      .single()

    if (error) throw error
    res.json(data)
  } catch (err) { next(err) }
})

// PUT /api/agents/:id
agentRoutes.put('/:id', async (req, res, next) => {
  try {
    const updates = {}
    const allowed = ['display_name', 'purpose', 'agent_md', 'knowledge_md', 'context_md', 'model', 'is_active']
    for (const key of allowed) {
      if (req.body[key] !== undefined) updates[key] = req.body[key]
    }
    updates.updated_at = new Date().toISOString()

    const { data, error } = await supabase
      .from('agents')
      .update(updates)
      .eq('id', req.params.id)
      .eq('user_id', req.userId)
      .select()
      .single()

    if (error) throw error
    res.json(data)
  } catch (err) { next(err) }
})

// DELETE /api/agents/:id
agentRoutes.delete('/:id', async (req, res, next) => {
  try {
    const { error } = await supabase
      .from('agents')
      .delete()
      .eq('id', req.params.id)
      .eq('user_id', req.userId)

    if (error) throw error
    res.json({ deleted: true })
  } catch (err) { next(err) }
})

// GET /api/agents/:id/messages
agentRoutes.get('/:id/messages', async (req, res, next) => {
  try {
    const page = parseInt(req.query.page) || 1
    const limit = 50
    const offset = (page - 1) * limit

    const { data, error, count } = await supabase
      .from('messages')
      .select('*', { count: 'exact' })
      .eq('agent_id', req.params.id)
      .eq('user_id', req.userId)
      .order('created_at', { ascending: true })
      .range(offset, offset + limit - 1)

    if (error) throw error
    res.json({ messages: data || [], total: count || 0 })
  } catch (err) { next(err) }
})

// GET /api/agents/:id/memory
agentRoutes.get('/:id/memory', async (req, res, next) => {
  try {
    const { data, error } = await supabase
      .from('user_facts')
      .select('*')
      .eq('user_id', req.userId)
      .eq('is_active', true)
      .or(`agent_id.eq.${req.params.id},agent_id.is.null`)
      .order('created_at', { ascending: false })

    if (error) throw error
    res.json({ facts: data || [] })
  } catch (err) { next(err) }
})

// DELETE /api/agents/:id/memory/:factId
agentRoutes.delete('/:id/memory/:factId', async (req, res, next) => {
  try {
    const { error } = await supabase
      .from('user_facts')
      .update({ is_active: false })
      .eq('id', req.params.factId)
      .eq('user_id', req.userId)

    if (error) throw error
    res.json({ deleted: true })
  } catch (err) { next(err) }
})

// POST /api/agents/:id/test — send a test message via the runtime
agentRoutes.post('/:id/test', async (req, res, next) => {
  try {
    const { message } = validateMessage(req.body)

    const { data: agent, error: agentErr } = await supabase
      .from('agents')
      .select('*')
      .eq('id', req.params.id)
      .eq('user_id', req.userId)
      .single()
    if (agentErr) throw agentErr

    const { data: profile } = await supabase
      .from('user_profiles')
      .select('profile_text')
      .eq('user_id', req.userId)
      .single()

    // Fetch recent conversation history + relevant memory in parallel
    const [recentMsgsResult, memoryProfile] = await Promise.all([
      supabase
        .from('messages')
        .select('role, content')
        .eq('agent_id', req.params.id)
        .eq('user_id', req.userId)
        .order('created_at', { ascending: false })
        .limit(20),
      getUserMemoryProfile(req.userId, message),
    ])
    const recentMsgs = recentMsgsResult.data

    const systemParts = []
    // Agent identity first — defines who the agent is and how it behaves
    systemParts.push(`=== AGENT IDENTITY ===\n${agent.agent_md}`)
    if (agent.knowledge_md) systemParts.push(`=== KNOWLEDGE ===\n${agent.knowledge_md}`)
    if (agent.context_md) systemParts.push(`=== CURRENT STATE ===\n${agent.context_md}`)
    // User context — who you're talking to
    if (profile?.profile_text) systemParts.push(`=== USER PROFILE ===\n${profile.profile_text}`)
    // Memory — what you've learned across past conversations
    if (memoryProfile.staticProfile) systemParts.push(`=== WHAT YOU KNOW ABOUT THIS USER ===\n${memoryProfile.staticProfile}`)
    if (memoryProfile.dynamicContext) systemParts.push(`=== RECENT CONTEXT ===\n${memoryProfile.dynamicContext}`)
    systemParts.push(`=== CURRENT DATE & TIME ===\n${new Date().toISOString()}`)

    const systemPrompt = systemParts.join('\n\n')
    const history = (recentMsgs || []).reverse().map(m => ({ role: m.role, content: m.content }))

    await checkBillingLimit(req.userId, supabase)

    const client = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY })

    const claudePromise = client.messages.create({
      model: agent.model || 'claude-sonnet-4-6',
      max_tokens: 4096,
      system: systemPrompt,
      messages: [...history, { role: 'user', content: message }],
    })

    const timeoutPromise = new Promise((_, reject) =>
      setTimeout(() => reject(Object.assign(new Error('AI service timeout. Please try again.'), { status: 503 })), 30000)
    )

    const claudeResponse = await Promise.race([claudePromise, timeoutPromise])

    const responseText = claudeResponse.content[0].text

    // Fire-and-forget — never block the response on a DB write
    supabase.from('messages').insert([
      { user_id: req.userId, agent_id: req.params.id, channel_id: 'web', role: 'user', content: message },
      { user_id: req.userId, agent_id: req.params.id, channel_id: 'web', role: 'assistant', content: responseText },
    ]).then(({ error }) => {
      if (error) console.error('Message insert failed (non-fatal):', error.message)
    })

    // Store conversation to memory — fire and forget, never block the response
    addMemory(
      req.userId,
      `User: ${message}\n${agent.display_name}: ${responseText}`,
      { agentId: req.params.id, agentName: agent.display_name }
    ).catch(err => console.error('Memory store failed (non-fatal):', err.message))

    await supabase.from('usage_log').insert({
      user_id: req.userId,
      agent_id: req.params.id,
      provider: 'anthropic',
      model: agent.model || 'claude-sonnet-4-6',
      input_tokens: claudeResponse.usage?.input_tokens || 0,
      output_tokens: claudeResponse.usage?.output_tokens || 0,
      cost_usd: ((claudeResponse.usage?.input_tokens || 0) * 0.000003 + (claudeResponse.usage?.output_tokens || 0) * 0.000015),
    })

    res.json({ response: responseText })
  } catch (err) { next(err) }
})
