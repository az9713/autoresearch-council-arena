/**
 * Stage2.jsx — Anonymous rankings visualization + per-model vote breakdown.
 * Adapted from karpathy/llm-council frontend Stage2.jsx pattern.
 */
import { useState } from 'react'

const LABELS = { A: 'Proposal A', B: 'Proposal B', C: 'Proposal C', D: 'Proposal D', E: 'Current (baseline)' }
const COLORS = { A: '#7c8ff0', B: '#4ade80', C: '#f59e0b', D: '#f87171', E: '#94a3b8' }

export default function Stage2({ rankings, votes, modelNames }) {
  const [expandedVote, setExpandedVote] = useState(null)

  if (!rankings || rankings.length === 0) {
    return <Empty message="Waiting for Stage 2 rankings..." />
  }

  // Normalize scores: best avg_position = highest "street cred"
  const maxPos = Math.max(...rankings.map(r => r.avg_position))
  const streetCred = rankings.map(r => ({
    ...r,
    cred: Math.round(((maxPos - r.avg_position) / (maxPos || 1)) * 100),
  }))

  return (
    <div>
      <h2 style={styles.heading}>Stage 2 — Anonymous Peer Rankings</h2>
      <p style={styles.sub}>
        Each model ranked all versions anonymously (labels shuffled each iteration to prevent positional bias).
        Lower avg position = ranked higher by peers.
      </p>

      {/* Aggregate bar chart */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12, maxWidth: 600 }}>
        {streetCred.map((r, i) => (
          <div key={r.letter} style={{
            ...styles.row,
            borderColor: r.letter === 'E' ? '#2a2f4a' : COLORS[r.letter],
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, flex: 1 }}>
              <span style={{
                width: 28, height: 28, borderRadius: '50%',
                background: COLORS[r.letter] || '#4a5168',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 12, fontWeight: 700, color: '#fff', flexShrink: 0,
              }}>
                {i + 1}
              </span>
              <div>
                <div style={{ fontWeight: 600, fontSize: 14, color: '#e2e8f0' }}>
                  {LABELS[r.letter] || `Version ${r.letter}`}
                </div>
                <div style={{ fontSize: 11, color: '#4a5168' }}>
                  {r.letter !== 'E' && modelNames?.[r.letter] ? modelNames[r.letter] : r.letter === 'E' ? 'current artifact' : ''}
                </div>
                <div style={{ fontSize: 12, color: '#8892b0' }}>
                  avg position {r.avg_position.toFixed(2)} · {r.votes} vote{r.votes !== 1 ? 's' : ''}
                </div>
              </div>
            </div>

            {/* Street cred bar */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, width: 160 }}>
              <div style={{
                flex: 1, height: 8, background: '#1e2438', borderRadius: 4, overflow: 'hidden',
              }}>
                <div style={{
                  width: `${r.cred}%`, height: '100%',
                  background: COLORS[r.letter] || '#4a5168',
                  borderRadius: 4, transition: 'width 0.4s ease',
                }} />
              </div>
              <span style={{ fontSize: 12, fontWeight: 600, color: COLORS[r.letter], width: 32 }}>
                {r.cred}
              </span>
            </div>
          </div>
        ))}
      </div>

      <p style={{ marginTop: 12, fontSize: 12, color: '#4a5168' }}>
        "Street cred": normalized inverse of average rank position. Version E = current artifact (baseline to beat).
      </p>

      {/* Individual votes breakdown */}
      {votes && votes.length > 0 && (
        <div style={{ marginTop: 28 }}>
          <h3 style={{ fontSize: 15, fontWeight: 700, color: '#e2e8f0', marginBottom: 12 }}>
            Individual Votes
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {votes.map((vote, i) => (
              <div key={i} style={styles.voteCard}>
                <div
                  style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', cursor: 'pointer' }}
                  onClick={() => setExpandedVote(expandedVote === i ? null : i)}
                >
                  <div>
                    <div style={{ fontSize: 13, fontWeight: 600, color: '#a5b4fc' }}>
                      {vote.model}
                    </div>
                    <div style={{ fontSize: 12, color: '#8892b0', marginTop: 3, fontFamily: 'monospace' }}>
                      {vote.original_ranking}
                    </div>
                    <div style={{ fontSize: 11, color: '#4a5168', marginTop: 2 }}>
                      (anonymized: {vote.display_ranking})
                    </div>
                  </div>
                  <span style={{ fontSize: 12, color: '#4a5168', marginLeft: 12, flexShrink: 0 }}>
                    {expandedVote === i ? '▲ hide reasoning' : '▼ show reasoning'}
                  </span>
                </div>

                {expandedVote === i && vote.reasoning && (
                  <div style={{
                    marginTop: 12, paddingTop: 12, borderTop: '1px solid #2a2f4a',
                    fontSize: 13, color: '#cbd5e1', lineHeight: 1.6,
                    whiteSpace: 'pre-wrap',
                  }}>
                    {vote.reasoning}
                  </div>
                )}
                {expandedVote === i && !vote.reasoning && (
                  <div style={{ marginTop: 8, fontSize: 12, color: '#4a5168', fontStyle: 'italic' }}>
                    No reasoning captured.
                  </div>
                )}
              </div>
            ))}
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
  row: {
    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
    background: '#161b2e', border: '1px solid #2a2f4a',
    borderRadius: 10, padding: '14px 16px', gap: 16,
  },
  voteCard: {
    background: '#161b2e', border: '1px solid #2a2f4a',
    borderRadius: 10, padding: '14px 16px',
  },
}
