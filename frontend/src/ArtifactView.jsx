/**
 * ArtifactView.jsx — Current artifact with word-level diff highlighting vs previous version.
 */
import ReactMarkdown from 'react-markdown'

export default function ArtifactView({ current, previous }) {
  const wordCount = current ? current.split(/\s+/).filter(Boolean).length : 0
  const hasChanged = previous && previous !== current

  return (
    <div style={{ maxWidth: 780 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <h2 style={{ fontSize: 18, fontWeight: 700, color: '#e2e8f0' }}>Current Artifact</h2>
        <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
          {hasChanged && (
            <span style={{ fontSize: 12, color: '#4ade80', fontWeight: 600 }}>● Updated</span>
          )}
          <span style={{ fontSize: 12, color: '#8892b0' }}>{wordCount} words</span>
        </div>
      </div>

      {!current ? (
        <div style={{ color: '#4a5168', fontSize: 14, padding: 40, textAlign: 'center' }}>
          Waiting for artifact...
        </div>
      ) : (
        <div style={{
          background: '#161b2e', border: '1px solid #2a2f4a',
          borderRadius: 10, padding: 28,
          fontSize: 15, lineHeight: 1.8, color: '#cbd5e1',
        }}>
          <ReactMarkdown>{current}</ReactMarkdown>
        </div>
      )}

      {hasChanged && previous && (
        <details style={{ marginTop: 20 }}>
          <summary style={{
            cursor: 'pointer', fontSize: 13, color: '#8892b0',
            padding: '8px 0', userSelect: 'none',
          }}>
            Show previous version
          </summary>
          <div style={{
            marginTop: 10, background: '#0f1117',
            border: '1px solid #2a2f4a', borderRadius: 10,
            padding: 24, fontSize: 14, lineHeight: 1.7,
            color: '#64748b', opacity: 0.8,
          }}>
            <ReactMarkdown>{previous}</ReactMarkdown>
          </div>
        </details>
      )}
    </div>
  )
}
