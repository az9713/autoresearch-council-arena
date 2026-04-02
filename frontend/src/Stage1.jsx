/**
 * Stage1.jsx — Tabbed display of council proposals.
 * Adapted from karpathy/llm-council frontend Stage1.jsx pattern.
 */
import { useState } from 'react'
import ReactMarkdown from 'react-markdown'

const MODEL_LABELS = { A: 'Model A', B: 'Model B', C: 'Model C', D: 'Model D' }
const COLORS = { A: '#7c8ff0', B: '#4ade80', C: '#f59e0b', D: '#f87171' }

export default function Stage1({ proposals }) {
  const [active, setActive] = useState('A')

  if (!proposals) {
    return <Empty message="Waiting for Stage 1 proposals..." />
  }

  const letters = Object.keys(proposals)

  return (
    <div>
      <h2 style={styles.heading}>Stage 1 — Competing Proposals</h2>
      <p style={styles.sub}>
        {letters.length} models proposed improvements in parallel. Anonymous in Stage 2.
      </p>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 6, marginBottom: 20 }}>
        {letters.map(l => (
          <button key={l} onClick={() => setActive(l)} style={{
            ...styles.tab,
            background: active === l ? COLORS[l] : '#1e2438',
            color: active === l ? '#fff' : '#8892b0',
          }}>
            {MODEL_LABELS[l] || `Model ${l}`}
          </button>
        ))}
      </div>

      {/* Proposal content */}
      {proposals[active] && (
        <div style={styles.card}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 12 }}>
            <span style={{ color: COLORS[active], fontWeight: 600, fontSize: 13 }}>
              {MODEL_LABELS[active] || `Version ${active}`}
            </span>
            <span style={{ color: '#4a5168', fontSize: 12 }}>
              {proposals[active].split(/\s+/).length} words
            </span>
          </div>
          <div style={styles.prose}>
            <ReactMarkdown>{proposals[active]}</ReactMarkdown>
          </div>
        </div>
      )}
    </div>
  )
}

function Empty({ message }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: 200 }}>
      <p style={{ color: '#4a5168', fontSize: 14 }}>{message}</p>
    </div>
  )
}

const styles = {
  heading: { fontSize: 18, fontWeight: 700, marginBottom: 6, color: '#e2e8f0' },
  sub: { fontSize: 13, color: '#8892b0', marginBottom: 20 },
  tab: {
    padding: '6px 14px', borderRadius: 6, border: 'none',
    cursor: 'pointer', fontSize: 13, fontWeight: 500, transition: 'background 0.15s',
  },
  card: {
    background: '#161b2e', border: '1px solid #2a2f4a',
    borderRadius: 10, padding: 20,
  },
  prose: {
    fontSize: 14, lineHeight: 1.7, color: '#cbd5e1',
    '& p': { marginBottom: '1em' },
  },
}
