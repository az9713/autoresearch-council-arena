/**
 * Stage3.jsx — Chairman verdict, score, critique, and full response.
 * Adapted from karpathy/llm-council frontend Stage3.jsx pattern.
 */
import { useState } from 'react'
import ReactMarkdown from 'react-markdown'

const WINNER_LABELS = {
  A: 'Proposal A', B: 'Proposal B', C: 'Proposal C', D: 'Proposal D',
  E: 'Current artifact (no improvement this round)',
}
const WINNER_COLORS = { A: '#7c8ff0', B: '#4ade80', C: '#f59e0b', D: '#f87171', E: '#94a3b8' }

export default function Stage3({ data }) {
  const [showFullResponse, setShowFullResponse] = useState(false)

  if (!data) {
    return <Empty message="Waiting for Stage 3 verdict..." />
  }

  const {
    winner, council_score, sub_scores, critique,
    chairman_full_response, chairman_model,
    winner_model, model_names,
    confirmed_status,
  } = data

  const color = WINNER_COLORS[winner] || '#7c8ff0'
  const isConfirmed = !!confirmed_status
  const isKeep = isConfirmed ? confirmed_status === 'KEEP' : false

  return (
    <div style={{ maxWidth: 700 }}>
      <h2 style={styles.heading}>Stage 3 — Chairman's Verdict</h2>
      <p style={styles.sub}>
        Chairman: <span style={{ color: '#a5b4fc' }}>{chairman_model || 'unknown'}</span>
        {' '}· reviewed all proposals, peer rankings, and the current baseline.
      </p>

      {/* Score + winner banner */}
      <div style={{ ...styles.banner, borderColor: color, background: `${color}12` }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          {/* Score dial */}
          <div style={{
            width: 72, height: 72, borderRadius: '50%',
            border: `4px solid ${color}`,
            display: 'flex', flexDirection: 'column',
            alignItems: 'center', justifyContent: 'center', flexShrink: 0,
          }}>
            <span style={{ fontSize: 22, fontWeight: 800, color }}>{council_score}</span>
            <span style={{ fontSize: 10, color: '#8892b0' }}>/ 100</span>
          </div>

          <div>
            <div style={{ fontSize: 13, color: '#8892b0', marginBottom: 2 }}>Winner</div>
            <div style={{ fontSize: 16, fontWeight: 700, color }}>
              {WINNER_LABELS[winner] || `Version ${winner}`}
            </div>
            {winner !== 'E' && winner_model && (
              <div style={{ fontSize: 11, color: '#4a5168', marginTop: 2 }}>
                {winner_model}
              </div>
            )}
            <div style={{
              marginTop: 6, fontSize: 12, fontWeight: 600,
              color: isConfirmed
                ? (isKeep ? '#4ade80' : '#f87171')
                : winner === 'E' ? '#f87171' : '#fbbf24',
            }}>
              {isConfirmed
                ? (isKeep ? '✓ KEEP — artifact updated' : '✗ DISCARD — no improvement')
                : winner === 'E'
                  ? '✗ DISCARD — current artifact was best'
                  : '⏳ Pending — awaiting score confirmation from run.py'}
            </div>
          </div>
        </div>
      </div>

      {/* Sub-score breakdown */}
      {sub_scores && Object.keys(sub_scores).length > 0 && (
        <div style={styles.card}>
          <h3 style={styles.cardHeading}>Score Breakdown (0–20 per dimension)</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {Object.entries(sub_scores).map(([dim, val]) => (
              <div key={dim} style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <span style={{ fontSize: 11, color: '#8892b0', width: 110, flexShrink: 0 }}>
                  {dim.replace(/_/g, ' ')}
                </span>
                <div style={{ flex: 1, background: '#0d1117', borderRadius: 4, height: 10, overflow: 'hidden' }}>
                  <div style={{
                    width: `${(val / 20) * 100}%`,
                    height: '100%',
                    background: val >= 16 ? '#4ade80' : val >= 12 ? '#f59e0b' : '#f87171',
                    borderRadius: 4,
                    transition: 'width 0.4s ease',
                  }} />
                </div>
                <span style={{ fontSize: 12, fontWeight: 700, color: '#cbd5e1', width: 30, textAlign: 'right' }}>
                  {val}/20
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Critique */}
      {critique && (
        <div style={styles.card}>
          <h3 style={styles.cardHeading}>Chairman's Critique</h3>
          <div style={styles.prose}>
            <ReactMarkdown>{critique}</ReactMarkdown>
          </div>
        </div>
      )}

      {/* Full chairman response */}
      {chairman_full_response && (
        <div style={{ ...styles.card, marginTop: 16 }}>
          <div
            style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', cursor: 'pointer' }}
            onClick={() => setShowFullResponse(v => !v)}
          >
            <h3 style={{ ...styles.cardHeading, marginBottom: 0 }}>Chairman's Full Response</h3>
            <span style={{ fontSize: 12, color: '#4a5168' }}>
              {showFullResponse ? '▲ collapse' : '▼ expand'}
            </span>
          </div>
          {showFullResponse && (
            <div style={{ ...styles.prose, marginTop: 12, whiteSpace: 'pre-wrap', fontFamily: 'monospace', fontSize: 12 }}>
              {chairman_full_response}
            </div>
          )}
        </div>
      )}

      {/* Model name legend */}
      {model_names && Object.keys(model_names).length > 0 && (
        <div style={{ ...styles.card, marginTop: 16 }}>
          <h3 style={styles.cardHeading}>Council Model Assignment</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {Object.entries(model_names).map(([letter, model]) => (
              <div key={letter} style={{ display: 'flex', gap: 12, fontSize: 12 }}>
                <span style={{ fontWeight: 700, color: WINNER_COLORS[letter], width: 20 }}>{letter}</span>
                <span style={{ color: '#cbd5e1' }}>{model}</span>
                {letter === winner && <span style={{ color: '#4ade80' }}>← winner</span>}
              </div>
            ))}
            <div style={{ display: 'flex', gap: 12, fontSize: 12, marginTop: 4, paddingTop: 8, borderTop: '1px solid #2a2f4a' }}>
              <span style={{ fontWeight: 700, color: '#94a3b8', width: 20 }}>E</span>
              <span style={{ color: '#cbd5e1' }}>current artifact (baseline)</span>
              {winner === 'E' && <span style={{ color: '#94a3b8' }}>← winner</span>}
            </div>
            <div style={{ display: 'flex', gap: 12, fontSize: 12, paddingTop: 4 }}>
              <span style={{ fontWeight: 700, color: '#a5b4fc', width: 20 }}>★</span>
              <span style={{ color: '#cbd5e1' }}>{chairman_model} (chairman)</span>
            </div>
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
  banner: {
    border: '1px solid', borderRadius: 12,
    padding: '20px 24px', marginBottom: 20,
  },
  card: {
    background: '#161b2e', border: '1px solid #2a2f4a',
    borderRadius: 10, padding: 20,
  },
  cardHeading: { fontSize: 14, fontWeight: 600, color: '#8892b0', marginBottom: 12 },
  prose: { fontSize: 14, lineHeight: 1.7, color: '#cbd5e1' },
}
