/**
 * ─── MEMORY SERVICE ──────────────────────────────────────────────────────────
 *
 * Abstraction layer over whatever memory backend we're using.
 * All agent code calls THIS file — never the provider directly.
 *
 * CURRENT PROVIDER: Supermemory (supermemory.ai)
 *
 * ─── HOW TO MIGRATE TO DIY pgvector (when the time comes) ───────────────────
 *
 * 1. Add pgvector to Supabase (one click in the dashboard)
 * 2. Run the migration schema (see bottom of this file)
 * 3. Export all memories from Supermemory:
 *      await exportAllMemories(userId) — iterates all container memories
 * 4. Embed each memory (OpenAI text-embedding-3-small, $0.02/1M tokens)
 * 5. Insert into pgvector table
 * 6. Set MEMORY_PROVIDER=pgvector in server .env
 * 7. Implement the pgvector functions below (stubs already there)
 * 8. Done. Zero changes to routes or agent logic.
 *
 * The interface contract never changes — only the implementation swaps.
 * ─────────────────────────────────────────────────────────────────────────────
 */

const PROVIDER = process.env.MEMORY_PROVIDER || 'supermemory'
const SUPERMEMORY_API = 'https://api.supermemory.ai'
const SUPERMEMORY_KEY = process.env.SUPERMEMORY_API_KEY

if (PROVIDER === 'supermemory' && !SUPERMEMORY_KEY) {
  throw new Error('SUPERMEMORY_API_KEY is required when MEMORY_PROVIDER=supermemory')
}

// ─── Public interface (never changes) ────────────────────────────────────────

/**
 * Store a memory after a conversation turn.
 * Call this fire-and-forget after saving messages to DB.
 *
 * @param {string} userId
 * @param {string} content  - The conversation turn (user + agent combined)
 * @param {object} metadata - Optional: agentId, agentName, timestamp
 */
export async function addMemory(userId, content, metadata = {}) {
  if (PROVIDER === 'supermemory') return _supermemoryAdd(userId, content, metadata)
  // if (PROVIDER === 'pgvector') return _pgvectorAdd(userId, content, metadata)
  throw new Error(`Unknown memory provider: ${PROVIDER}`)
}

/**
 * Get relevant memories for the current conversation turn.
 * Returns a formatted string ready to inject into a system prompt.
 *
 * @param {string} userId
 * @param {string} query   - The user's current message
 * @returns {string}       - Formatted memories, empty string if none
 */
export async function getRelevantMemory(userId, query) {
  if (PROVIDER === 'supermemory') return _supermemorySearch(userId, query)
  // if (PROVIDER === 'pgvector') return _pgvectorSearch(userId, query)
  throw new Error(`Unknown memory provider: ${PROVIDER}`)
}

/**
 * Get the user's full memory profile — stable facts + recent context.
 * Richer than search, used at conversation start.
 *
 * @param {string} userId
 * @param {string} query   - Current message for relevance scoring
 * @returns {{ staticProfile: string, dynamicContext: string }}
 */
export async function getUserMemoryProfile(userId, query) {
  if (PROVIDER === 'supermemory') return _supermemoryProfile(userId, query)
  // if (PROVIDER === 'pgvector') return _pgvectorProfile(userId, query)
  throw new Error(`Unknown memory provider: ${PROVIDER}`)
}

/**
 * Export all memories for a user. Used for migration.
 * @param {string} userId
 * @returns {Array} raw memory objects
 */
export async function exportAllMemories(userId) {
  if (PROVIDER === 'supermemory') return _supermemoryExport(userId)
  throw new Error('exportAllMemories only implemented for supermemory provider')
}


// ─── Supermemory adapter ──────────────────────────────────────────────────────

async function _supermemoryFetch(path, body) {
  const res = await fetch(`${SUPERMEMORY_API}${path}`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${SUPERMEMORY_KEY}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`Supermemory ${path} failed (${res.status}): ${text}`)
  }
  return res.json()
}

async function _supermemoryAdd(userId, content, metadata) {
  await _supermemoryFetch('/v3/documents', {
    content,
    containerTag: userId,
    metadata: {
      agentId: metadata.agentId || '',
      agentName: metadata.agentName || '',
      timestamp: metadata.timestamp || new Date().toISOString(),
    },
  })
}

async function _supermemorySearch(userId, query) {
  try {
    const data = await _supermemoryFetch('/v3/search', {
      query,
      containerTag: userId,
      limit: 10,
    })
    if (!data?.results?.length) return ''
    const lines = data.results
      .filter(r => (r.score ?? 1) > 0.6)
      .map(r => `- ${r.content || r.document?.content || ''}`)
      .filter(Boolean)
      .join('\n')
    return lines || ''
  } catch (err) {
    console.error('Memory search failed (non-fatal):', err.message)
    return '' // memory failure should never block a conversation
  }
}

async function _supermemoryProfile(userId, query) {
  try {
    const data = await _supermemoryFetch('/v3/search', {
      query,
      containerTag: userId,
      limit: 20,
    })
    const results = data?.results || []
    // Split into recent (last 7 days) and older facts
    const now = Date.now()
    const week = 7 * 24 * 60 * 60 * 1000
    const recent = []
    const older = []
    for (const r of results) {
      const ts = r.metadata?.timestamp ? new Date(r.metadata.timestamp).getTime() : 0
      const content = r.content || r.document?.content || ''
      if (!content) continue
      if (now - ts < week) recent.push(`- ${content}`)
      else older.push(`- ${content}`)
    }
    return {
      staticProfile: older.join('\n'),
      dynamicContext: recent.join('\n'),
    }
  } catch (err) {
    console.error('Memory profile failed (non-fatal):', err.message)
    return { staticProfile: '', dynamicContext: '' }
  }
}

async function _supermemoryExport(userId) {
  const memories = []
  let page = 1
  while (true) {
    const data = await _supermemoryFetch('/v3/documents/list', {
      containerTag: userId,
      pagination: { page, pageSize: 100 },
    })
    const docs = data?.documents || []
    memories.push(...docs)
    if (docs.length < 100) break
    page++
  }
  return memories
}


// ─── pgvector adapter (stubs — implement when migrating) ─────────────────────
//
// async function _pgvectorAdd(userId, content, metadata) {
//   const embedding = await _embed(content)
//   await supabase.from('memories').insert({
//     user_id: userId,
//     content,
//     embedding,
//     agent_id: metadata.agentId,
//     created_at: new Date().toISOString(),
//   })
// }
//
// async function _pgvectorSearch(userId, query) {
//   const embedding = await _embed(query)
//   const { data } = await supabase.rpc('match_memories', {
//     query_embedding: embedding,
//     match_user_id: userId,
//     match_threshold: 0.7,
//     match_count: 15,
//   })
//   return data?.map(r => `- ${r.content}`).join('\n') || ''
// }
//
// async function _pgvectorProfile(userId, query) {
//   const relevant = await _pgvectorSearch(userId, query)
//   return { staticProfile: relevant, dynamicContext: '' }
// }
//
// async function _embed(text) {
//   // OpenAI text-embedding-3-small — $0.02/1M tokens
//   const res = await fetch('https://api.openai.com/v1/embeddings', {
//     method: 'POST',
//     headers: { 'Authorization': `Bearer ${process.env.OPENAI_API_KEY}`, 'Content-Type': 'application/json' },
//     body: JSON.stringify({ model: 'text-embedding-3-small', input: text }),
//   })
//   const data = await res.json()
//   return data.data[0].embedding
// }


// ─── Migration SQL (run in Supabase when switching to pgvector) ───────────────
//
// CREATE EXTENSION IF NOT EXISTS vector;
//
// CREATE TABLE memories (
//   id          uuid DEFAULT gen_random_uuid() PRIMARY KEY,
//   user_id     uuid REFERENCES users(id) ON DELETE CASCADE,
//   agent_id    uuid REFERENCES agents(id) ON DELETE SET NULL,
//   content     text NOT NULL,
//   embedding   vector(1536),
//   is_latest   boolean DEFAULT true,
//   created_at  timestamptz DEFAULT now()
// );
//
// CREATE INDEX ON memories USING hnsw (embedding vector_cosine_ops);
// CREATE INDEX ON memories (user_id, is_latest);
//
// -- Semantic search function
// CREATE OR REPLACE FUNCTION match_memories(
//   query_embedding vector(1536),
//   match_user_id   uuid,
//   match_threshold float,
//   match_count     int
// )
// RETURNS TABLE(id uuid, content text, similarity float)
// LANGUAGE plpgsql AS $$
// BEGIN
//   RETURN QUERY
//   SELECT m.id, m.content,
//     1 - (m.embedding <=> query_embedding) AS similarity
//   FROM memories m
//   WHERE m.user_id = match_user_id
//     AND m.is_latest = true
//     AND 1 - (m.embedding <=> query_embedding) > match_threshold
//   ORDER BY similarity DESC
//   LIMIT match_count;
// END; $$;
