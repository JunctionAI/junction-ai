import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../../lib/api'

const STEPS = ['Goal', 'Expertise', 'Communication', 'Preview']

const DOMAINS = [
  { id: 'work', label: 'Work / Business', icon: '💼', name: 'Business Coach' },
  { id: 'health', label: 'Health & Fitness', icon: '⚡', name: 'Health Coach' },
  { id: 'mind', label: 'Mental Wellbeing', icon: '🧠', name: 'Wellbeing Coach' },
  { id: 'learning', label: 'Learning & Skills', icon: '📚', name: 'Learning Coach' },
  { id: 'finance', label: 'Finance & Wealth', icon: '📈', name: 'Finance Coach' },
  { id: 'social', label: 'Relationships', icon: '👥', name: 'Life Coach' },
  { id: 'custom', label: 'Custom', icon: '⭐', name: 'Personal Agent' },
]

const PERSONALITIES = [
  { id: 'coaching', name: 'Coach', desc: 'Pushes you, celebrates wins, holds the standard' },
  { id: 'mentor', name: 'Mentor', desc: 'Wise, experienced, thought-provoking guidance' },
  { id: 'casual', name: 'Friend', desc: 'Warm, honest, real — like a mate who tells it straight' },
  { id: 'strategic', name: 'Strategist', desc: 'Analytical, big-picture, systems-oriented' },
  { id: 'professional', name: 'Expert', desc: 'Precise, focused, evidence-based' },
]

const CHECKIN_STYLES = [
  { id: 'brief_update', name: 'Brief check-in', desc: 'Quick status — what did you do today?' },
  { id: 'deep_reflection', name: 'Deep reflection', desc: 'Wins, struggles, what\'s holding you back' },
  { id: 'task_reminder', name: 'Task focus', desc: 'What\'s on your list? Let\'s prioritise' },
  { id: 'full_briefing', name: 'Full briefing', desc: 'Goals, metrics, blockers, next steps' },
]

function buildSchedule(form: ReturnType<typeof defaultForm>) {
  const [h, m] = form.check_in_time.split(':')
  const hour = parseInt(h)
  const crons: Record<string, string> = {
    twice_daily: `${m} ${h},${(hour + 12) % 24} * * *`,
    daily: `${m} ${h} * * *`,
    every_2_days: `${m} ${h} */2 * *`,
    weekly: `${m} ${h} * * 1`,
  }
  const stylePrompts: Record<string, string> = {
    brief_update: 'Send a brief check-in. Ask one focused question about progress toward their goal.',
    deep_reflection: 'Send a deep reflection prompt. Ask about wins, struggles, and what\'s blocking them.',
    task_reminder: 'Review their priorities and help them decide what to work on next.',
    full_briefing: 'Send a full briefing covering their goals, recent progress, blockers, and what needs attention.',
  }
  return {
    cron_expression: crons[form.check_in_frequency] || crons.daily,
    task_prompt: `${stylePrompts[form.check_in_style] || ''} User's dream outcome: "${form.dream_outcome}".`,
    description: `${form.display_name} ${form.check_in_frequency.replace(/_/g, ' ')} check-in`,
  }
}

function defaultForm() {
  return {
    goal_domain: '',
    dream_outcome: '',
    display_name: '',
    inspirations: '',
    expertise: '',
    knowledge: '',
    personality: 'coaching',
    check_in_frequency: 'daily',
    check_in_time: '09:00',
    check_in_style: 'brief_update',
    accountability_level: 50,
    has_schedule: true,
    show_knowledge: false,
    first_message: '',
    first_message_loading: false,
    first_message_error: '',
  }
}

export function AgentCreateWizard() {
  const navigate = useNavigate()
  const [step, setStep] = useState(0)
  const [creating, setCreating] = useState(false)
  const [form, setForm] = useState(defaultForm)
  const previewFired = useRef(false)

  const update = (key: string, value: unknown) =>
    setForm(prev => ({ ...prev, [key]: value }))

  // Fire preview when reaching step 3
  useEffect(() => {
    if (step !== 3 || previewFired.current || form.first_message) return
    previewFired.current = true
    update('first_message_loading', true)
    update('first_message_error', '')
    api.previewFirstMessage({
      display_name: form.display_name,
      purpose: form.dream_outcome,
      personality: form.personality,
      goal_domain: form.goal_domain,
      dream_outcome: form.dream_outcome,
      inspirations: form.inspirations,
      expertise: form.expertise,
      accountability_level: form.accountability_level,
      check_in_style: form.check_in_style,
    }).then(({ first_message }) => {
      update('first_message', first_message)
      update('first_message_loading', false)
    }).catch(err => {
      update('first_message_error', err.message)
      update('first_message_loading', false)
    })
  }, [step])

  const regeneratePreview = () => {
    previewFired.current = false
    update('first_message', '')
    update('first_message_loading', false)
    update('first_message_error', '')
    // Re-trigger by bumping step away and back
    setStep(2)
    setTimeout(() => setStep(3), 50)
  }

  const create = async () => {
    setCreating(true)
    try {
      const agent = await api.createAgent({
        display_name: form.display_name,
        purpose: form.dream_outcome,
        personality: form.personality,
        knowledge: form.knowledge || undefined,
        goal_domain: form.goal_domain,
        dream_outcome: form.dream_outcome,
        inspirations: form.inspirations,
        expertise: form.expertise,
        accountability_level: form.accountability_level,
        check_in_frequency: form.check_in_frequency,
        check_in_style: form.check_in_style,
        schedule: form.has_schedule ? buildSchedule(form) : undefined,
      })
      navigate(`/agents/${agent.id}`)
    } catch (err) {
      console.error('Create agent error:', err)
      alert('Failed to create agent. Please try again.')
    } finally {
      setCreating(false)
    }
  }

  const canNext = () => {
    if (step === 0) return form.goal_domain !== '' && form.dream_outcome.length > 10
    if (step === 1) return form.display_name.length > 0
    return true
  }

  const accountabilityHint = form.accountability_level >= 61
    ? 'Hard accountability — I\'ll call out patterns and excuses directly'
    : form.accountability_level >= 31
    ? 'Balanced — I\'ll encourage and challenge in equal measure'
    : 'Gentle — I\'ll ask questions and celebrate every step forward'

  return (
    <div className="page">
      <div className="wizard" style={{ maxWidth: 640 }}>

        <div className="wizard-steps">
          {STEPS.map((_, i) => (
            <div key={i} className={`wizard-step ${i === step ? 'active' : i < step ? 'done' : ''}`} />
          ))}
        </div>

        <p style={{ fontSize: 11, color: 'var(--text-dim)', textAlign: 'center', marginBottom: 24, letterSpacing: 2, textTransform: 'uppercase' }}>
          {STEPS[step]}
        </p>

        {/* Step 0 — Goal */}
        {step === 0 && (
          <>
            <h1>What's this agent for?</h1>
            <p className="subtitle">Pick a domain, then define the dream outcome. This shapes everything about how your agent thinks and what it holds you to.</p>

            <div className="domain-grid">
              {DOMAINS.map(d => (
                <div
                  key={d.id}
                  className={`domain-option${form.goal_domain === d.id ? ' selected' : ''}`}
                  onClick={() => {
                    update('goal_domain', d.id)
                    if (!form.display_name) update('display_name', d.name)
                  }}
                >
                  <div className="domain-icon">{d.icon}</div>
                  <div className="domain-name">{d.label}</div>
                </div>
              ))}
            </div>

            <div className="field">
              <label>What's the dream outcome?</label>
              <textarea
                value={form.dream_outcome}
                onChange={e => update('dream_outcome', e.target.value)}
                placeholder="Be specific. e.g. Launch my SaaS to $10k MRR by December. Get to 85kg by July. Build a daily reading habit."
                rows={3}
              />
              <div className="field-hint">Your agent will reference this by name and build everything around it.</div>
            </div>
          </>
        )}

        {/* Step 1 — Expertise */}
        {step === 1 && (
          <>
            <h1>Build your agent's character</h1>
            <p className="subtitle">The best agents feel like a specific person — someone with real expertise, a clear philosophy, and a way of thinking that resonates with you.</p>

            <div className="field">
              <label>Agent name</label>
              <input
                value={form.display_name}
                onChange={e => update('display_name', e.target.value)}
                placeholder="e.g. Business Coach, Titan, Marcus"
              />
            </div>

            <div className="field">
              <label>Who inspires you in this area?</label>
              <input
                value={form.inspirations}
                onChange={e => update('inspirations', e.target.value)}
                placeholder="e.g. Alex Hormozi, James Clear, Naval Ravikant, Tim Ferriss"
              />
              <div className="field-hint">Your agent will think and communicate through the lens of these people.</div>
            </div>

            <div className="field">
              <label>What should your agent be an expert in?</label>
              <textarea
                value={form.expertise}
                onChange={e => update('expertise', e.target.value)}
                placeholder="e.g. Growth marketing, cold outreach, SaaS pricing, habit formation, compound strength training..."
                rows={3}
              />
            </div>

            <div className="field">
              <label>Personality</label>
              <div className="personality-grid">
                {PERSONALITIES.map(p => (
                  <div
                    key={p.id}
                    className={`personality-option${form.personality === p.id ? ' selected' : ''}`}
                    onClick={() => update('personality', p.id)}
                  >
                    <div className="name">{p.name}</div>
                    <div style={{ fontSize: 11, color: 'var(--text-dim)', marginTop: 4 }}>{p.desc}</div>
                  </div>
                ))}
              </div>
            </div>

            <div className="field">
              <button
                type="button"
                onClick={() => update('show_knowledge', !form.show_knowledge)}
                style={{ background: 'none', border: 'none', color: 'var(--text-dim)', fontSize: 13, cursor: 'pointer', padding: 0, textDecoration: 'underline' }}
              >
                {form.show_knowledge ? '— Hide' : '+ Add'} custom knowledge
              </button>
              {form.show_knowledge && (
                <textarea
                  value={form.knowledge}
                  onChange={e => update('knowledge', e.target.value)}
                  placeholder="Paste any SOPs, playbooks, frameworks, or specific instructions. This becomes a skill file the agent reads before every response."
                  rows={8}
                  style={{ fontFamily: 'monospace', fontSize: 13, marginTop: 12 }}
                />
              )}
            </div>
          </>
        )}

        {/* Step 2 — Communication */}
        {step === 2 && (
          <>
            <h1>How should it check in?</h1>
            <p className="subtitle">Your agent will message you on a schedule you control. This is the accountability engine.</p>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
              <div className="field">
                <label>Frequency</label>
                <select value={form.check_in_frequency} onChange={e => update('check_in_frequency', e.target.value)}>
                  <option value="twice_daily">Twice daily</option>
                  <option value="daily">Daily</option>
                  <option value="every_2_days">Every 2 days</option>
                  <option value="weekly">Weekly</option>
                </select>
              </div>
              <div className="field">
                <label>Time</label>
                <input type="time" value={form.check_in_time} onChange={e => update('check_in_time', e.target.value)} />
              </div>
            </div>

            <div className="field">
              <label>Check-in style</label>
              <div className="checkin-grid">
                {CHECKIN_STYLES.map(s => (
                  <div
                    key={s.id}
                    className={`checkin-option${form.check_in_style === s.id ? ' selected' : ''}`}
                    onClick={() => update('check_in_style', s.id)}
                  >
                    <div className="checkin-name">{s.name}</div>
                    <div className="checkin-desc">{s.desc}</div>
                  </div>
                ))}
              </div>
            </div>

            <div className="field">
              <label>Accountability level</label>
              <input
                type="range" min="0" max="100"
                value={form.accountability_level}
                onChange={e => update('accountability_level', +e.target.value)}
              />
              <div className="accountability-labels">
                <span>Gentle</span>
                <span>Hard</span>
              </div>
              <p className="accountability-hint">{accountabilityHint}</p>
            </div>
          </>
        )}

        {/* Step 3 — Preview */}
        {step === 3 && (
          <>
            <h1>Meet your agent</h1>
            <p className="subtitle">This is how {form.display_name || 'your agent'} will introduce themselves. Powered by Claude Opus.</p>

            {form.first_message_loading && (
              <div className="preview-loading">
                <p>Your agent is writing their intro...</p>
                <p style={{ fontSize: 12, marginTop: 8, opacity: 0.6 }}>This takes about 10 seconds</p>
              </div>
            )}

            {form.first_message_error && (
              <div style={{ background: 'rgba(239,68,68,0.1)', color: '#ef4444', padding: '12px 16px', borderRadius: 8, marginBottom: 20, fontSize: 13 }}>
                Error: {form.first_message_error}
              </div>
            )}

            {form.first_message && !form.first_message_loading && (
              <>
                <div className="preview-message">{form.first_message}</div>
                <button
                  type="button"
                  onClick={regeneratePreview}
                  style={{ background: 'none', border: 'none', color: 'var(--text-dim)', fontSize: 13, cursor: 'pointer', textDecoration: 'underline', marginBottom: 24, display: 'block' }}
                >
                  Regenerate
                </button>
              </>
            )}

            <div className="card" style={{ marginBottom: 24, fontSize: 13 }}>
              <p style={{ color: 'var(--text-dim)', marginBottom: 4 }}>Goal</p>
              <p style={{ color: 'var(--text-h)' }}>{form.dream_outcome}</p>
              <p style={{ color: 'var(--text-dim)', marginTop: 12, marginBottom: 4 }}>Schedule</p>
              <p style={{ color: 'var(--text-h)' }}>
                {form.check_in_frequency.replace(/_/g, ' ')} at {form.check_in_time} · {CHECKIN_STYLES.find(s => s.id === form.check_in_style)?.name}
              </p>
            </div>
          </>
        )}

        {/* Actions */}
        <div className="wizard-actions">
          {step > 0 ? (
            <button className="btn btn-secondary" onClick={() => setStep(s => s - 1)}>Back</button>
          ) : <div />}

          {step < STEPS.length - 1 ? (
            <button className="btn btn-primary" onClick={() => setStep(s => s + 1)} disabled={!canNext()}>
              Continue
            </button>
          ) : (
            <button
              className="btn btn-gradient btn-lg"
              onClick={create}
              disabled={creating || form.first_message_loading}
            >
              {creating ? 'Creating...' : `Create ${form.display_name || 'Agent'}`}
            </button>
          )}
        </div>

      </div>
    </div>
  )
}
