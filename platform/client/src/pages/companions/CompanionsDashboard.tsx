import { useEffect, useState, useCallback } from 'react'
import './CompanionsDashboard.css'

interface DayUsage {
  input_tokens: number
  output_tokens: number
  calls: number
  model: string
}

interface AgentUsage {
  _total_input_tokens: number
  _total_output_tokens: number
  _total_cost_usd: number
  [date: string]: DayUsage | number
}

interface Product {
  name: string
  dose: string
  phase: number
  category: string
  priority: string
  notes: string
  companions: { slug: string; user: string; phase: number }[]
}

interface PhaseConfig {
  name: string
  key: string
  description: string
}

interface Companion {
  name: string
  user: string
  slug: string
  description: string
  phases: PhaseConfig[]
  currentPhase: string
  phaseNumber: number
  daysInPhase: number
  activeDays7d: number
  usage: AgentUsage | null
  products: Product[]
}

interface DashboardData {
  companions: Record<string, Companion>
  products: Record<string, Product>
  last_updated: string
  error?: string
}

export function CompanionsDashboard() {
  const [data, setData] = useState<DashboardData | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'overview' | 'products'>('overview')

  const fetchData = useCallback(async () => {
    try {
      const resp = await fetch('/api/companions/status')
      if (resp.ok) {
        setData(await resp.json())
        setError(null)
      } else {
        setError('Could not reach companion data')
      }
    } catch {
      setError('Dashboard offline — is the server running?')
    }
  }, [])

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 15_000)
    return () => clearInterval(interval)
  }, [fetchData])

  const companions = data?.companions ? Object.values(data.companions) : []
  const products = data?.products ? Object.values(data.products) : []

  // Aggregate costs
  const totalCost = companions.reduce((sum, c) => sum + (c.usage?._total_cost_usd || 0), 0)
  const totalCalls = companions.reduce((sum, c) => {
    if (!c.usage) return sum
    return sum + Object.entries(c.usage).reduce((s, [k, v]) => {
      if (k.startsWith('_') || typeof v === 'number') return s
      return s + (v as DayUsage).calls
    }, 0)
  }, 0)

  // Unique products across companions
  const supplementProducts = products.filter(p => p.category === 'supplement')
  const nutritionProducts = products.filter(p => p.category === 'nutrition')
  const highPriority = products.filter(p => p.priority === 'high')

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1>Recovery Companions</h1>
          <p className="rc-subtitle">AI health companions — API costs, recovery progress, and fulfillment planning</p>
        </div>
        <div className="rc-tab-bar">
          <button className={`rc-tab ${activeTab === 'overview' ? 'active' : ''}`} onClick={() => setActiveTab('overview')}>Overview</button>
          <button className={`rc-tab ${activeTab === 'products' ? 'active' : ''}`} onClick={() => setActiveTab('products')}>Products & Fulfillment</button>
        </div>
      </div>

      {error && <div className="rc-error">{error}</div>}

      {activeTab === 'overview' && (
        <>
          {/* Aggregate metrics */}
          <div className="rc-metrics-row">
            <div className="card rc-metric-card">
              <div className="rc-metric-label">Total API Spend</div>
              <div className="rc-metric-value rc-accent">${totalCost.toFixed(4)}</div>
              <div className="rc-metric-sub">across all companions</div>
            </div>
            <div className="card rc-metric-card">
              <div className="rc-metric-label">API Calls</div>
              <div className="rc-metric-value">{totalCalls}</div>
              <div className="rc-metric-sub">conversations total</div>
            </div>
            <div className="card rc-metric-card">
              <div className="rc-metric-label">Active Companions</div>
              <div className="rc-metric-value">{companions.length}</div>
              <div className="rc-metric-sub">Jackson + Tyler</div>
            </div>
            <div className="card rc-metric-card">
              <div className="rc-metric-label">Fulfillable Products</div>
              <div className="rc-metric-value">{highPriority.length}</div>
              <div className="rc-metric-sub">high-priority supplements</div>
            </div>
          </div>

          {/* Per-companion cards */}
          {companions.map(comp => {
            const usage = comp.usage
            const agentCost = usage?._total_cost_usd || 0
            const agentCalls = usage ? Object.entries(usage).reduce((s, [k, v]) => {
              if (k.startsWith('_') || typeof v === 'number') return s
              return s + (v as DayUsage).calls
            }, 0) : 0

            const dailyData = usage ? Object.entries(usage)
              .filter(([k]) => !k.startsWith('_') && k.includes('-'))
              .sort(([a], [b]) => b.localeCompare(a))
              .slice(0, 7)
              .map(([date, d]) => {
                const day = d as DayUsage
                const isOpus = day.model?.includes('opus')
                const cost = isOpus
                  ? (day.input_tokens * 15.0 / 1_000_000) + (day.output_tokens * 75.0 / 1_000_000)
                  : (day.input_tokens * 3.0 / 1_000_000) + (day.output_tokens * 15.0 / 1_000_000)
                return { date, ...day, cost }
              }) : []

            return (
              <div key={comp.slug} className="card rc-companion-card">
                <div className="rc-companion-header">
                  <div>
                    <h3>{comp.name} — {comp.user}</h3>
                    <p className="rc-companion-desc">{comp.description}</p>
                  </div>
                  <div className="rc-companion-stats">
                    <span className="rc-stat">Phase {comp.phaseNumber}: {comp.currentPhase}</span>
                    <span className="rc-stat">Day {comp.daysInPhase}</span>
                    <span className="rc-stat">{comp.activeDays7d}/7 active</span>
                  </div>
                </div>

                {/* Phase timeline */}
                <div className="rc-phases">
                  {comp.phases.map((phase, i) => (
                    <div key={phase.key} className={`rc-phase ${i + 1 < comp.phaseNumber ? 'rc-phase-done' : i + 1 === comp.phaseNumber ? 'rc-phase-active' : 'rc-phase-future'}`}>
                      <div className="rc-phase-dot" />
                      <div className="rc-phase-info">
                        <span className="rc-phase-name">{phase.name}</span>
                        <span className="rc-phase-desc">{phase.description}</span>
                      </div>
                    </div>
                  ))}
                </div>

                {/* API costs */}
                <div className="rc-cost-section">
                  <div className="rc-cost-header">
                    <h4>API Costs</h4>
                    <span className="rc-cost-total">${agentCost.toFixed(4)} total — {agentCalls} calls</span>
                  </div>
                  {dailyData.length === 0 ? (
                    <p className="rc-empty">No usage data yet — will populate after first check-in</p>
                  ) : (
                    <div className="rc-spend-table">
                      <div className="rc-spend-header">
                        <span>Date</span>
                        <span>Calls</span>
                        <span>Tokens</span>
                        <span>Cost</span>
                      </div>
                      {dailyData.map(d => (
                        <div key={d.date} className="rc-spend-row">
                          <span>{d.date}</span>
                          <span>{d.calls}</span>
                          <span>{(d.input_tokens + d.output_tokens).toLocaleString()}</span>
                          <span className="rc-accent">${d.cost.toFixed(4)}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )
          })}
        </>
      )}

      {activeTab === 'products' && (
        <>
          <div className="card rc-products-intro">
            <h3>Fulfillment Opportunity</h3>
            <p>Products recommended to companions through evidence-based protocols. These are potential fulfillment items — supplements and nutrition products the bot recommends as part of recovery plans.</p>
            <div className="rc-product-summary">
              <div className="rc-product-stat">
                <span className="rc-product-stat-value">{supplementProducts.length}</span>
                <span className="rc-product-stat-label">Supplements</span>
              </div>
              <div className="rc-product-stat">
                <span className="rc-product-stat-value">{nutritionProducts.length}</span>
                <span className="rc-product-stat-label">Nutrition</span>
              </div>
              <div className="rc-product-stat">
                <span className="rc-product-stat-value">{highPriority.length}</span>
                <span className="rc-product-stat-label">High Priority</span>
              </div>
              <div className="rc-product-stat">
                <span className="rc-product-stat-value">{companions.length}</span>
                <span className="rc-product-stat-label">Active Users</span>
              </div>
            </div>
          </div>

          {/* Supplements */}
          <div className="card rc-product-category">
            <h3>Supplements</h3>
            {supplementProducts.map(product => (
              <div key={product.name} className={`rc-product-row rc-priority-${product.priority}`}>
                <div className="rc-product-main">
                  <span className="rc-product-name">{product.name}</span>
                  <span className={`rc-priority-badge rc-priority-${product.priority}`}>{product.priority}</span>
                </div>
                <div className="rc-product-dose">{product.dose}</div>
                <div className="rc-product-notes">{product.notes}</div>
                <div className="rc-product-users">
                  {product.companions.map(c => (
                    <span key={c.slug} className="rc-product-user-tag">{c.user} (Phase {c.phase}+)</span>
                  ))}
                </div>
              </div>
            ))}
          </div>

          {/* Nutrition */}
          <div className="card rc-product-category">
            <h3>Nutrition Products</h3>
            {nutritionProducts.map(product => (
              <div key={product.name} className={`rc-product-row rc-priority-${product.priority}`}>
                <div className="rc-product-main">
                  <span className="rc-product-name">{product.name}</span>
                  <span className={`rc-priority-badge rc-priority-${product.priority}`}>{product.priority}</span>
                </div>
                <div className="rc-product-dose">{product.dose}</div>
                <div className="rc-product-notes">{product.notes}</div>
                <div className="rc-product-users">
                  {product.companions.map(c => (
                    <span key={c.slug} className="rc-product-user-tag">{c.user}</span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </>
      )}

      <div className="rc-footer-note">
        Auto-refreshes every 15 seconds — data from ~/tom-command-center/data/
      </div>
    </div>
  )
}
