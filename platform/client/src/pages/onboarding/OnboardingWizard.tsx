import { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../../lib/api'

const STEPS = ['You', 'Dream', 'Rhythm', 'Connect', 'Review']

// ─── VoiceCapture Component ───────────────────────────────────────────────────
interface VoiceCaptureProps {
  label: string
  value: string
  onChange: (v: string) => void
  placeholder: string
  rows?: number
}

function VoiceCapture({ label, value, onChange, placeholder, rows = 4 }: VoiceCaptureProps) {
  const [recording, setRecording] = useState(false)
  const [transcribing, setTranscribing] = useState(false)
  const [status, setStatus] = useState('')
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const chunksRef = useRef<Blob[]>([])

  const hasVoice = typeof window !== 'undefined' && !!window.MediaRecorder

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mimeType = MediaRecorder.isTypeSupported('audio/webm') ? 'audio/webm' : 'audio/mp4'
      const mr = new MediaRecorder(stream, { mimeType })
      chunksRef.current = []
      mr.ondataavailable = e => { if (e.data.size > 0) chunksRef.current.push(e.data) }
      mr.onstop = async () => {
        stream.getTracks().forEach(t => t.stop())
        setTranscribing(true)
        setStatus('Transcribing...')
        try {
          const ext = mimeType.includes('webm') ? 'recording.webm' : 'recording.mp4'
          const blob = new Blob(chunksRef.current, { type: mimeType })
          const { transcript } = await api.transcribeVoice(blob, ext)
          onChange(value ? `${value} ${transcript}` : transcript)
          setStatus('')
        } catch {
          setStatus('Transcription failed — try again')
        } finally {
          setTranscribing(false)
        }
      }
      mr.start()
      mediaRecorderRef.current = mr
      setRecording(true)
      setStatus('Recording... tap again to stop')
    } catch {
      setStatus('Microphone access denied')
    }
  }

  const stopRecording = () => {
    mediaRecorderRef.current?.stop()
    mediaRecorderRef.current = null
    setRecording(false)
  }

  const toggle = () => recording ? stopRecording() : startRecording()

  return (
    <div className="field">
      <label>{label}</label>
      <div className="voice-field-wrapper">
        <textarea
          value={value}
          onChange={e => onChange(e.target.value)}
          placeholder={placeholder}
          rows={rows}
        />
        {hasVoice && (
          <button
            type="button"
            className={`voice-btn${recording ? ' recording' : ''}`}
            onClick={toggle}
            disabled={transcribing}
            title={recording ? 'Stop recording' : 'Speak your answer'}
          >
            {recording ? (
              <svg viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="6" width="12" height="12" rx="2"/></svg>
            ) : (
              <svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2a3 3 0 0 1 3 3v7a3 3 0 0 1-6 0V5a3 3 0 0 1 3-3zm-1 16.93A8 8 0 0 1 4 11H2a10 10 0 0 0 9 9.93V23h2v-2.07A10 10 0 0 0 22 11h-2a8 8 0 0 1-7 7.93z"/></svg>
            )}
          </button>
        )}
      </div>
      {status && <p className={`voice-status${recording || transcribing ? ' active' : ''}`}>{status}</p>}
      {hasVoice && !status && <p className="voice-status">Tap the mic to speak your answer</p>}
    </div>
  )
}

// ─── Main Wizard ──────────────────────────────────────────────────────────────
export function OnboardingWizard() {
  const navigate = useNavigate()
  const [step, setStep] = useState(0)
  const hasCompiled = useRef(false)
  const [compiledProfile, setCompiledProfile] = useState('')
  const [compiling, setCompiling] = useState(false)

  const [answers, setAnswers] = useState({
    name: '',
    situation: '',
    dream_outcome: '',
    struggling_with: '',
    wake_time: '07:00',
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    telegram_code: '',
    telegram_verified: false,
  })

  const update = (key: string, value: unknown) =>
    setAnswers(prev => ({ ...prev, [key]: value }))

  const canNext = () => {
    if (step === 0) return answers.name.length > 0 && answers.situation.length > 10
    if (step === 1) return answers.dream_outcome.length > 10
    return true // steps 2, 3, 4 always continuable
  }

  const verifyTelegram = async () => {
    try {
      const result = await api.verifyTelegram(answers.telegram_code)
      if (result.verified) update('telegram_verified', true)
    } catch {
      alert('Invalid code. Make sure you sent /start to @JunctionAIBot first.')
    }
  }

  const goToReview = async () => {
    setStep(STEPS.length - 1)
    if (hasCompiled.current) return
    hasCompiled.current = true
    setCompiling(true)
    try {
      const raw_answers = {
        name: answers.name,
        situation: answers.situation,
        dream_outcome: answers.dream_outcome,
        struggling_with: answers.struggling_with,
        wake_time: answers.wake_time,
        timezone: answers.timezone,
      }
      await api.updateProfile({ raw_answers })
      const { profile_text } = await api.compileProfile()
      setCompiledProfile(profile_text)
    } catch (err) {
      console.error('Compile error:', err)
      setCompiledProfile('Something went wrong building your profile. You can still continue.')
    } finally {
      setCompiling(false)
    }
  }

  const isReviewStep = step === STEPS.length - 1
  const isTelegramStep = step === 3

  return (
    <div className="wizard">
      <div className="wizard-steps">
        {STEPS.map((_, i) => (
          <div key={i} className={`wizard-step ${i === step ? 'active' : i < step ? 'done' : ''}`} />
        ))}
      </div>

      <p style={{ fontSize: 11, color: 'var(--text-dim)', textAlign: 'center', marginBottom: 24, letterSpacing: 2, textTransform: 'uppercase' }}>
        {STEPS[step]}
      </p>

      {/* Step 0 — About You */}
      {step === 0 && (
        <>
          <h1>Let's get to know you</h1>
          <p className="subtitle">This builds the foundation every agent you create will share. Speak freely — Claude structures it for you.</p>
          <p className="privacy-note"><svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4z"/></svg>Your answers are encrypted and never shared. Only your agents can read them.</p>

          <div className="field">
            <label>Your name</label>
            <input value={answers.name} onChange={e => update('name', e.target.value)} placeholder="e.g. Tom" />
          </div>

          <VoiceCapture
            label="What's your current situation?"
            value={answers.situation}
            onChange={v => update('situation', v)}
            placeholder="Be real — what's going on in your life right now? Work, money, energy, relationships. The more honest, the more useful your agents become."
            rows={5}
          />
        </>
      )}

      {/* Step 1 — Dream */}
      {step === 1 && (
        <div className="wizard-step">
          <h2>What does winning look like?</h2>
          <p className="subtitle">Be specific — this is what your agents will hold you to.</p>
          <p className="privacy-note"><svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4z"/></svg>For your agents only. Never shared or used to train models.</p>

          <VoiceCapture
            label="What would you need to achieve in the next 6-12 months to call it a win?"
            placeholder="e.g. Launch my product to $10k MRR, lose 15kg and keep it off, double my income..."
            value={answers.dream_outcome}
            onChange={v => setAnswers(a => ({ ...a, dream_outcome: v }))}
            rows={4}
          />

          <VoiceCapture
            label="What's blocking you right now?"
            placeholder="e.g. I procrastinate on hard things, I run out of energy mid-day, I avoid difficult conversations..."
            value={answers.struggling_with}
            onChange={v => setAnswers(a => ({ ...a, struggling_with: v }))}
            rows={3}
          />
        </div>
      )}

      {/* Step 2 — Rhythm */}
      {step === 2 && (
        <div className="wizard-step">
          <h2>Your rhythm</h2>
          <p className="subtitle">Your agents check in during your waking hours — not at 3am.</p>
          <p className="privacy-note"><svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4z"/></svg>Only used for scheduling. Never shared.</p>

          <div className="form-group">
            <label className="form-label">What time do you wake up?</label>
            <input
              type="time"
              className="form-control"
              value={answers.wake_time}
              onChange={e => setAnswers(a => ({ ...a, wake_time: e.target.value }))}
            />
          </div>

          <div className="form-group">
            <label className="form-label">Your timezone</label>
            <select
              className="form-control"
              value={answers.timezone}
              onChange={e => setAnswers(a => ({ ...a, timezone: e.target.value }))}
            >
              <option value="Pacific/Auckland">Auckland (NZST)</option>
              <option value="Australia/Sydney">Sydney (AEST)</option>
              <option value="Asia/Singapore">Singapore (SGT)</option>
              <option value="Asia/Tokyo">Tokyo (JST)</option>
              <option value="Europe/London">London (GMT)</option>
              <option value="Europe/Paris">Paris (CET)</option>
              <option value="America/New_York">New York (EST)</option>
              <option value="America/Chicago">Chicago (CST)</option>
              <option value="America/Denver">Denver (MST)</option>
              <option value="America/Los_Angeles">Los Angeles (PST)</option>
              <option value="America/Toronto">Toronto (EST)</option>
              <option value="America/Vancouver">Vancouver (PST)</option>
            </select>
          </div>
        </div>
      )}

      {/* Step 3 — Connect (Telegram) */}
      {step === 3 && (
        <>
          <h1>Connect Telegram</h1>
          <p className="subtitle">Your agents communicate via Telegram. Let's link your account.</p>
          <p className="privacy-note"><svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4z"/></svg>We only store your Telegram chat ID to deliver messages. We can't read your other chats.</p>

          {!answers.telegram_verified ? (
            <>
              <div className="card" style={{ marginBottom: 16 }}>
                <p style={{ color: 'var(--text-h)', marginBottom: 8, fontWeight: 500 }}>Step 1</p>
                <p>Open Telegram and search for <strong style={{ color: 'var(--accent)' }}>@JunctionAIBot</strong></p>
                <p style={{ marginTop: 4 }}>Send the message: <code style={{ background: 'var(--bg-input)', padding: '2px 6px', borderRadius: 4 }}>/start</code></p>
              </div>

              <div className="card">
                <p style={{ color: 'var(--text-h)', marginBottom: 8, fontWeight: 500 }}>Step 2</p>
                <p style={{ marginBottom: 12 }}>Enter the 6-digit code the bot sends you:</p>
                <div style={{ display: 'flex', gap: 8 }}>
                  <input value={answers.telegram_code} onChange={e => update('telegram_code', e.target.value)}
                    placeholder="123456" maxLength={6} style={{ flex: 1, fontSize: 20, textAlign: 'center', letterSpacing: 8 }} />
                  <button className="btn btn-primary" onClick={verifyTelegram} disabled={answers.telegram_code.length !== 6}>
                    Verify
                  </button>
                </div>
              </div>

              <p style={{ textAlign: 'center', marginTop: 20 }}>
                <button onClick={() => setStep(s => s + 1)} style={{ background: 'none', border: 'none', color: 'var(--text-dim)', fontSize: 13, cursor: 'pointer', textDecoration: 'underline' }}>
                  Skip for now
                </button>
              </p>
            </>
          ) : (
            <div className="card" style={{ textAlign: 'center', padding: 40 }}>
              <div style={{ fontSize: 40, marginBottom: 12 }}>✓</div>
              <p style={{ color: 'var(--accent)', fontWeight: 500 }}>Telegram connected</p>
              <p style={{ color: 'var(--text-dim)', marginTop: 8, fontSize: 13 }}>Your agents will reach you via @JunctionAIBot</p>
            </div>
          )}
        </>
      )}

      {/* Step 4 — Review */}
      {isReviewStep && (
        <>
          <h1>Your profile</h1>
          <p className="subtitle">Claude has built your context document. Every agent you create will start with this knowledge.</p>

          {compiling ? (
            <div className="preview-loading">
              <p>Claude is building your profile...</p>
              <p style={{ fontSize: 12, marginTop: 8, color: 'var(--text-dim)' }}>This takes about 15 seconds</p>
            </div>
          ) : compiledProfile ? (
            <div className="card" style={{ maxHeight: 400, overflowY: 'auto', marginBottom: 24 }}>
              <pre style={{ fontFamily: 'inherit', fontSize: 13, lineHeight: 1.7, color: 'var(--text-h)', whiteSpace: 'pre-wrap', margin: 0 }}>
                {compiledProfile}
              </pre>
            </div>
          ) : null}

          <p style={{ color: 'var(--text-dim)', fontSize: 13, marginBottom: 24 }}>
            You can update this anytime in Settings. Now let's create your first agent.
          </p>
        </>
      )}

      {/* Navigation */}
      <div className="wizard-actions">
        {step > 0 && !isReviewStep ? (
          <button className="btn btn-secondary" onClick={() => setStep(s => s - 1)}>Back</button>
        ) : <div />}

        {isReviewStep ? (
          <button className="btn btn-gradient btn-lg" onClick={() => navigate('/dashboard')} disabled={compiling}>
            {compiling ? 'Building your profile...' : 'Launch Dashboard →'}
          </button>
        ) : isTelegramStep ? (
          <button className="btn btn-primary" onClick={goToReview}>
            Continue
          </button>
        ) : (
          <button className="btn btn-primary" onClick={() => setStep(s => s + 1)} disabled={!canNext()}>
            Continue
          </button>
        )}
      </div>
    </div>
  )
}
