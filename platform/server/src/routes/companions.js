import { Router } from 'express'
import { readFileSync, existsSync } from 'fs'
import { join } from 'path'
import { homedir } from 'os'

export const companionRoutes = Router()

const CMD_CENTER = join(homedir(), 'tom-command-center')
const DATA_DIR = join(CMD_CENTER, 'data')
const AGENTS_DIR = join(CMD_CENTER, 'agents')

// Companion agent definitions
const COMPANIONS = {
  aether: {
    name: 'Aether',
    user: 'Jackson Crone',
    slug: 'aether',
    description: 'Recovery companion — FND, POTS, sensorimotor OCD, complex PTSD',
    phases: [
      { name: 'Foundation', key: 'foundation', description: 'Build trust, baseline metrics, psychoeducation, liquid nutrition' },
      { name: 'Nervous System Regulation', key: 'regulation', description: 'Break fear-symptom cycle, PRT, RF-ERP, vagal toning' },
      { name: 'Physical Rehabilitation', key: 'rehab', description: 'Modified Levine/Dallas Protocol, graded exercise, nutrition expansion' },
      { name: 'Expanding Capacity', key: 'expanding', description: 'Upright exercise, social reintegration, trauma processing support' },
      { name: 'Independence', key: 'independence', description: 'Self-management, flare protocol, maintenance' },
    ],
    products: [
      { name: 'Magnesium Glycinate', dose: '400-600mg daily', phase: 1, category: 'supplement', priority: 'high', notes: 'Neuroprotection, muscle relaxation, sleep support' },
      { name: 'Omega-3 Fish Oil (EPA/DHA)', dose: '2-4g daily', phase: 1, category: 'supplement', priority: 'high', notes: 'Anti-inflammatory, nerve cell membrane repair' },
      { name: 'Vitamin D3', dose: '2000-4000 IU daily', phase: 1, category: 'supplement', priority: 'high', notes: 'Neuroprotective, commonly deficient' },
      { name: 'B-Complex', dose: 'Daily', phase: 1, category: 'supplement', priority: 'high', notes: 'Nerve function, energy metabolism' },
      { name: 'Electrolyte Tablets', dose: '2-3g extra sodium/day', phase: 2, category: 'supplement', priority: 'medium', notes: 'POTS blood volume support' },
      { name: 'Zinc', dose: '15-30mg daily', phase: 2, category: 'supplement', priority: 'medium', notes: 'Immune, nerve repair' },
      { name: 'Protein Powder (Whey/Plant)', dose: '25g per shake', phase: 1, category: 'nutrition', priority: 'high', notes: 'Caloric rehabilitation, liquid-first approach' },
      { name: 'MCT Oil', dose: '1 tbsp per shake', phase: 1, category: 'nutrition', priority: 'medium', notes: 'Calorie-dense addition for weight gain' },
      { name: 'Nut Butter', dose: '2 tbsp per shake', phase: 1, category: 'nutrition', priority: 'medium', notes: 'Calorie-dense, protein source' },
    ],
  },
  forge: {
    name: 'Forge',
    user: 'Tyler Howarth',
    slug: 'forge',
    description: 'Brain recovery + physical transformation — post-concussion, substance recovery, ADHD',
    phases: [
      { name: 'Foundation', key: 'foundation', description: 'Baseline metrics, supplement optimization, structured routine' },
      { name: 'Brain Recovery', key: 'brain_recovery', description: 'Cognitive training, strength training, HRV biofeedback, sleep optimization' },
      { name: 'Physical Transformation', key: 'transformation', description: 'Hypertrophy training, surfing, body composition, social confidence' },
      { name: 'Cognitive Peak', key: 'cognitive_peak', description: 'Communication mastery, career exploration, relationship readiness' },
      { name: 'Superhuman', key: 'superhuman', description: 'Maintenance, continuous optimization, self-directed growth' },
    ],
    products: [
      { name: 'Magnesium Glycinate', dose: '400-600mg daily', phase: 1, category: 'supplement', priority: 'high', notes: 'Blood levels low-end (0.79). Brain + muscle recovery' },
      { name: 'Omega-3 Fish Oil (EPA/DHA)', dose: '3g daily', phase: 1, category: 'supplement', priority: 'high', notes: 'Already taking. Anti-inflammatory, brain repair' },
      { name: 'Creatine Monohydrate', dose: '5g daily', phase: 1, category: 'supplement', priority: 'high', notes: 'Neuroprotective, evidence for post-TBI cognitive improvement' },
      { name: 'NAC (N-Acetyl Cysteine)', dose: '600mg daily', phase: 1, category: 'supplement', priority: 'high', notes: 'Glutathione precursor, brain detox, substance recovery' },
      { name: 'Vitamin B12 Methylcobalamin', dose: '1000mcg sublingual', phase: 1, category: 'supplement', priority: 'high', notes: 'Blood shows 200.3 (suboptimal for brain recovery)' },
      { name: 'L-Glutamine', dose: '5g daily', phase: 1, category: 'supplement', priority: 'high', notes: 'Gut lining repair' },
      { name: 'Probiotics Multi-Strain', dose: '20+ billion CFU', phase: 1, category: 'supplement', priority: 'high', notes: 'Gut microbiome restoration post-substance use' },
      { name: 'L-Theanine', dose: '400mg daily', phase: 1, category: 'supplement', priority: 'medium', notes: 'Already taking. Calm focus, pairs with caffeine' },
      { name: 'Lion\'s Mane Mushroom', dose: 'Per label', phase: 1, category: 'supplement', priority: 'medium', notes: 'Already taking. NGF stimulation, neurogenesis' },
      { name: 'CoQ10', dose: '150-300mg daily', phase: 2, category: 'supplement', priority: 'medium', notes: 'Mitochondrial support, brain energy' },
      { name: 'Phosphatidylserine', dose: '200mg daily', phase: 2, category: 'supplement', priority: 'medium', notes: 'Memory, cortisol reduction' },
      { name: 'Whey Protein', dose: '30g per serving', phase: 2, category: 'nutrition', priority: 'high', notes: 'Hit 156g/day protein target for muscle gain' },
    ],
  },
}

// GET /api/companions/status — all companion data for dashboard
companionRoutes.get('/status', async (req, res) => {
  try {
    // Read API usage data
    let usage = null
    const usagePath = join(DATA_DIR, 'api_usage.json')
    if (existsSync(usagePath)) {
      usage = JSON.parse(readFileSync(usagePath, 'utf-8'))
    }

    // Read companion state data
    const companions = {}
    for (const [slug, config] of Object.entries(COMPANIONS)) {
      const contextPath = join(AGENTS_DIR, slug, 'state', 'CONTEXT.md')
      let context = null
      if (existsSync(contextPath)) {
        context = readFileSync(contextPath, 'utf-8')
      }

      // Extract current phase from CONTEXT.md
      let currentPhase = 'Foundation'
      let phaseNumber = 1
      let daysInPhase = 0
      if (context) {
        const phaseMatch = context.match(/CURRENT PHASE:\s*(.+?)(?:\s*\(Phase\s*(\d+)\))?$/m)
        if (phaseMatch) {
          currentPhase = phaseMatch[1].trim()
          phaseNumber = parseInt(phaseMatch[2]) || 1
        }
        const daysMatch = context.match(/Days in Phase:\s*(\d+)/i)
        if (daysMatch) {
          daysInPhase = parseInt(daysMatch[1])
        }
      }

      // Count session logs for last 7 days
      let activeDays = 0
      const stateDir = join(AGENTS_DIR, slug, 'state')
      for (let i = 1; i <= 7; i++) {
        const d = new Date()
        d.setDate(d.getDate() - i)
        const dateStr = d.toISOString().split('T')[0]
        if (existsSync(join(stateDir, `session-log-${dateStr}.md`))) {
          activeDays++
        }
      }

      companions[slug] = {
        ...config,
        currentPhase,
        phaseNumber,
        daysInPhase,
        activeDays7d: activeDays,
        usage: usage?.[slug] || null,
      }
    }

    // Aggregate product list across all companions
    const allProducts = {}
    for (const [slug, config] of Object.entries(COMPANIONS)) {
      for (const product of config.products) {
        const key = product.name
        if (!allProducts[key]) {
          allProducts[key] = {
            ...product,
            companions: [{ slug, user: config.user, phase: product.phase }],
          }
        } else {
          allProducts[key].companions.push({ slug, user: config.user, phase: product.phase })
        }
      }
    }

    res.json({
      companions,
      products: allProducts,
      last_updated: new Date().toISOString(),
    })
  } catch (err) {
    res.json({
      companions: {},
      products: {},
      last_updated: new Date().toISOString(),
      error: err.message,
    })
  }
})
