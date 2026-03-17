import { Router } from 'express'
import { supabase } from '../middleware/auth.js'
import Anthropic from '@anthropic-ai/sdk'
import multer from 'multer'
import OpenAI from 'openai'
import { toFile } from 'openai'
import { validateProfileAnswers } from '../middleware/validate.js'

export const profileRoutes = Router()

const upload = multer({ storage: multer.memoryStorage(), limits: { fileSize: 25 * 1024 * 1024 } })

// GET /api/profile
profileRoutes.get('/', async (req, res, next) => {
  try {
    const { data, error } = await supabase
      .from('user_profiles')
      .select('*')
      .eq('user_id', req.userId)
      .single()

    if (error && error.code !== 'PGRST116') throw error
    res.json(data || { profile_text: '', raw_answers: {} })
  } catch (err) { next(err) }
})

// PUT /api/profile — save onboarding answers
profileRoutes.put('/', async (req, res, next) => {
  try {
    const { raw_answers } = validateProfileAnswers(req.body)

    const { data, error } = await supabase
      .from('user_profiles')
      .upsert({
        user_id: req.userId,
        raw_answers,
        updated_at: new Date().toISOString(),
      }, { onConflict: 'user_id' })
      .select()
      .single()

    if (error) throw error

    await supabase.from('users').update({ onboarding_complete: true }).eq('id', req.userId)

    res.json(data)
  } catch (err) { next(err) }
})

// POST /api/profile/compile — compile raw answers into rich profile_text via Opus 4.6
profileRoutes.post('/compile', async (req, res, next) => {
  try {
    const { data: profile, error } = await supabase
      .from('user_profiles')
      .select('raw_answers')
      .eq('user_id', req.userId)
      .single()

    if (error) throw error

    const client = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY })
    const response = await client.messages.create({
      model: 'claude-opus-4-6',
      max_tokens: 3000,
      messages: [{
        role: 'user',
        content: `You are building a personal context document for an AI agent system. This document will be loaded into every AI agent this person ever creates, giving them deep background knowledge about the user.

Based on the onboarding answers below, write a rich, specific, insightful profile document in third person. Do NOT just reformat the answers — synthesise them. Surface what a great coach or mentor would notice. Be concrete and specific. Avoid generic statements.

Structure the output as markdown with these exact sections:

## Identity
Who they are, what they do, their background and current situation. What defines them.

## Situation Right Now
What's actually going on in their life currently — work, finances, relationships, energy. Be honest and specific.

## Goals
### Short-term (3–6 months)
### Medium-term (1–3 years)
### Long-term (5+ years)
Be specific about what success looks like for each horizon.

## Daily Schedule & Routine
When they wake, sleep, work, train. Weekly rhythm. What their days actually look like.

## Struggles & Blockers
What's genuinely hard for them. What patterns hold them back. What they've tried that hasn't worked and why.

## Communication Preferences
How they want to be talked to. Tone, format, frequency, what to avoid. Their communication style.

## Tools & Stack
What software, apps, and tools they use daily.

## What They've Tried
Relevant attempts, experiments, past approaches — successes and failures.

---

Onboarding data:
${JSON.stringify(profile.raw_answers, null, 2)}`
      }],
    })

    const profileText = response.content[0].text

    await supabase
      .from('user_profiles')
      .update({ profile_text: profileText, updated_at: new Date().toISOString() })
      .eq('user_id', req.userId)

    await supabase.from('usage_log').insert({
      user_id: req.userId,
      provider: 'anthropic',
      model: 'claude-opus-4-6',
      input_tokens: response.usage?.input_tokens || 0,
      output_tokens: response.usage?.output_tokens || 0,
      cost_usd: ((response.usage?.input_tokens || 0) * 0.000015 + (response.usage?.output_tokens || 0) * 0.000075),
    })

    res.json({ profile_text: profileText })
  } catch (err) { next(err) }
})

// POST /api/profile/voice — transcribe audio blob via OpenAI Whisper
const ALLOWED_AUDIO_TYPES = ['audio/webm', 'audio/mp4', 'audio/mpeg', 'audio/wav', 'audio/ogg', 'audio/m4a']

profileRoutes.post('/voice', upload.single('audio'), async (req, res, next) => {
  try {
    if (!req.file) return res.status(400).json({ error: 'No audio file provided' })

    // Validate file type — reject anything that isn't audio
    if (!ALLOWED_AUDIO_TYPES.includes(req.file.mimetype)) {
      return res.status(400).json({ error: 'Invalid file type. Audio files only.' })
    }

    const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY })

    // Use a safe filename, never trust user-supplied originalname
    const ext = req.file.mimetype.includes('mp4') || req.file.mimetype.includes('m4a') ? 'mp4' : 'webm'
    const safeFilename = `recording.${ext}`

    const audioFile = await toFile(req.file.buffer, safeFilename, {
      type: req.file.mimetype,
    })

    const result = await openai.audio.transcriptions.create({
      file: audioFile,
      model: 'whisper-1',
      language: 'en',
    })

    res.json({ transcript: result.text })
  } catch (err) { next(err) }
})

// DELETE /api/profile/account — deletes the authenticated user and all their data
profileRoutes.delete('/account', async (req, res, next) => {
  try {
    const userId = req.userId
    // Delete auth user (cascades to all FK-linked tables via Supabase)
    const { error } = await supabase.auth.admin.deleteUser(userId)
    if (error) throw error
    res.json({ success: true })
  } catch (err) { next(err) }
})
