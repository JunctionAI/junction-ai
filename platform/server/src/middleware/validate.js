/**
 * Input validation and sanitisation helpers.
 * All user inputs that end up in Claude system prompts must pass through here.
 */

// Strip characters that can be used for prompt injection
function sanitisePromptInput(value, maxLength = 500) {
  if (typeof value !== 'string') return ''
  return value
    .slice(0, maxLength)
    .replace(/\[INST\]|\[\/INST\]|<\|system\|>|<\|user\|>|<\|assistant\|>/gi, '') // LLM control tokens
    .trim()
}

// Validate and sanitise agent creation / preview fields
export function validateAgentInput(body) {
  const errors = []

  const display_name = sanitisePromptInput(body.display_name, 100)
  if (!display_name) errors.push('display_name is required')

  const purpose = sanitisePromptInput(body.purpose || body.dream_outcome, 1000)
  const goal_domain = sanitisePromptInput(body.goal_domain, 50)
  const dream_outcome = sanitisePromptInput(body.dream_outcome, 1000)
  const inspirations = sanitisePromptInput(body.inspirations, 300)
  const expertise = sanitisePromptInput(body.expertise, 500)
  const knowledge = sanitisePromptInput(body.knowledge, 10000)
  const personality = sanitisePromptInput(body.personality, 50)
  const check_in_style = sanitisePromptInput(body.check_in_style, 50)
  const check_in_frequency = sanitisePromptInput(body.check_in_frequency, 20)

  const accountability_level = Math.min(100, Math.max(0, parseInt(body.accountability_level) || 50))

  if (errors.length) throw Object.assign(new Error(errors.join(', ')), { status: 400 })

  return {
    display_name, purpose, goal_domain, dream_outcome,
    inspirations, expertise, knowledge, personality,
    check_in_style, check_in_frequency, accountability_level,
  }
}

// Validate profile answers
export function validateProfileAnswers(body) {
  if (!body.raw_answers || typeof body.raw_answers !== 'object') {
    throw Object.assign(new Error('raw_answers must be an object'), { status: 400 })
  }

  // Sanitise every string value in raw_answers
  const sanitised = {}
  for (const [key, value] of Object.entries(body.raw_answers)) {
    sanitised[key] = typeof value === 'string'
      ? sanitisePromptInput(value, 2000)
      : value
  }
  return { raw_answers: sanitised }
}

// Validate a chat message
export function validateMessage(body) {
  if (!body.message || typeof body.message !== 'string') {
    throw Object.assign(new Error('message is required'), { status: 400 })
  }
  return { message: sanitisePromptInput(body.message, 2000) }
}
