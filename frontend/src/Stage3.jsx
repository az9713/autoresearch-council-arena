/**
 * Stage3.jsx — Chairman verdict, score, and critique.
 * Adapted from karpathy/llm-council frontend Stage3.jsx pattern.
 */
import ReactMarkdown from 'react-markdown'

const WINNER_LABELS = {
  A: 'Proposal A', B: 'Proposal B', C: 'Proposal C', D: 'Proposal D',
  E: 'Current artifact (no improvement this round)',
}
const WINNER_COLORS = { A: '#7c8ff0', B: '#4ade80', C: '#f59e0b', D: '#f87171', E: '#94a3b8' }

export default function Stage3({ data }) {
  if (!data) {
    return <Empty message="Waiting for Stage 3 verdict..." />
  }

  const { winner, council_score, critique, confirmed_status } = data
  const color = WINNER_COLORS[winner] || '#7c8ff0'
  // confirmed_status ('KEEP'/'DISCARD') arrives via iteration_result event after run.py
  // decides. Before that, winner===E is always DISCARD; winner!==E is pending confirmation.
  const isConfirmed = !!confirmed_status
  const isKeep = isConfirmed ? confirmed_status === 'KEEP' : false

  return (
    <div style={{ maxWidth: 700 }}>
      <h2 style={styles.heading}>Stage 3 — Chairman's Verdict</h2>
      <p style={styles.sub}>
        The chairman reviewed all proposals, peer rankings, and the current baseline.
      </p>

      {/* Score + winner banner */}
      <div style={{
        ...styles.banner,
        borderColor: color,
        background: `${color}12`,
      }}>
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
            <div style={{ fontSize: 13, color: '#8892b0', marginBottom: 4 }}>Winner</div>
            <div style={{ fontSize: 16, fontWeight: 700, color }}>
              {WINNER_LABELS[winner] || `Version ${winner}`}
            </div>
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

      {/* Critique */}
      {critique && (
        <div style={styles.card}>
          <h3 style={{ fontSize: 14, fontWeight: 600, color: '#8892b0', marginBottom: 12 }}>
            Chairman's Critique
          </h3>
          <div style={styles.prose}>
            <ReactMarkdown>{critique}</ReactMarkdown>
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
  prose: { fontSize: 14, lineHeight: 1.7, color: '#cbd5e1' },
}
