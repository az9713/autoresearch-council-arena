/**
 * Stage2.jsx — Anonymous rankings visualization ("street cred" scores).
 * Adapted from karpathy/llm-council frontend Stage2.jsx pattern.
 */

const LABELS = { A: 'Proposal A', B: 'Proposal B', C: 'Proposal C', D: 'Proposal D', E: 'Current (baseline)' }
const COLORS = { A: '#7c8ff0', B: '#4ade80', C: '#f59e0b', D: '#f87171', E: '#94a3b8' }

export default function Stage2({ rankings }) {
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
        Each model ranked all versions anonymously (no model names visible). Lower avg position = ranked higher.
      </p>

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

      <p style={{ marginTop: 16, fontSize: 12, color: '#4a5168' }}>
        "Street cred" score: normalized inverse of average rank position.
        Version E is the current artifact (baseline to beat).
      </p>
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
}
