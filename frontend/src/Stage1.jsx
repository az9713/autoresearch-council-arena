/**
 * Stage1.jsx — All council proposals displayed simultaneously as cards.
 */
import ReactMarkdown from 'react-markdown'

const MODEL_LABELS = { A: 'Model A', B: 'Model B', C: 'Model C', D: 'Model D' }
const COLORS = { A: '#7c8ff0', B: '#4ade80', C: '#f59e0b', D: '#f87171' }

export default function Stage1({ proposals, modelNames }) {
  if (!proposals) {
    return <Empty message="Waiting for Stage 1 proposals..." />
  }

  const letters = Object.keys(proposals)

  return (
    <div>
      <h2 style={styles.heading}>Stage 1 — Competing Proposals</h2>
      <p style={styles.sub}>
        {letters.length} model{letters.length !== 1 ? 's' : ''} proposed improvements in parallel.
        Labels are shuffled anonymously in Stage 2 to prevent positional bias.
      </p>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
        {letters.map(l => (
          <div key={l} style={{ ...styles.card, borderColor: COLORS[l] || '#2a2f4a' }}>
            {/* Card header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 16 }}>
              <div>
                <span style={{ color: COLORS[l], fontWeight: 700, fontSize: 14 }}>
                  {MODEL_LABELS[l] || `Model ${l}`}
                </span>
                {modelNames?.[l] && (
                  <div style={{ color: '#4a5168', fontSize: 11, marginTop: 2 }}>
                    {modelNames[l]}
                  </div>
                )}
              </div>
              <span style={{ color: '#4a5168', fontSize: 12, flexShrink: 0, marginLeft: 12 }}>
                {proposals[l].split(/\s+/).filter(Boolean).length} words
              </span>
            </div>

            {/* Full proposal */}
            <div style={styles.prose}>
              <ReactMarkdown>{proposals[l]}</ReactMarkdown>
            </div>
          </div>
        ))}
      </div>
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
  sub: { fontSize: 13, color: '#8892b0', marginBottom: 24 },
  card: {
    background: '#161b2e', border: '1px solid',
    borderRadius: 10, padding: 20,
  },
  prose: {
    fontSize: 14, lineHeight: 1.7, color: '#cbd5e1',
  },
}
