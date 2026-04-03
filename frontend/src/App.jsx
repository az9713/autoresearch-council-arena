import { useState, useEffect, useRef } from 'react'
import Stage1 from './Stage1.jsx'
import Stage2 from './Stage2.jsx'
import Stage3 from './Stage3.jsx'
import ArtifactView from './ArtifactView.jsx'
import ResultsChart from './ResultsChart.jsx'

const API = ''  // proxied via vite

export default function App() {
  const [status, setStatus] = useState({ iteration: 0, best_score: 0, artifact_words: 0 })
  const [results, setResults] = useState([])
  const [artifact, setArtifact] = useState('')
  const [prevArtifact, setPrevArtifact] = useState('')

  // Current iteration stage data
  const [stage1Data, setStage1Data] = useState(null)   // { proposals, model_names }
  const [stage2Data, setStage2Data] = useState(null)   // { rankings, votes, model_names }
  const [stage3Data, setStage3Data] = useState(null)   // { winner, council_score, critique, ... }
  const [activeTab, setActiveTab] = useState('artifact')
  const [stopping, setStopping] = useState(false)
  const [runEnded, setRunEnded] = useState(null)  // { reason, iteration, best_score }

  const eventSourceRef = useRef(null)

  // Poll status + results every 5s
  useEffect(() => {
    const poll = async () => {
      try {
        const [s, r, a] = await Promise.all([
          fetch(`${API}/api/status`).then(r => r.json()),
          fetch(`${API}/api/results`).then(r => r.json()),
          fetch(`${API}/api/artifact`).then(r => r.json()),
        ])
        setStatus(s)
        setResults(r)
        setArtifact(prev => { setPrevArtifact(prev); return a.content })
      } catch (_) {}
    }
    poll()
    const id = setInterval(poll, 5000)
    return () => clearInterval(id)
  }, [])

  // SSE stream for live stage events
  useEffect(() => {
    const es = new EventSource(`${API}/api/stream`)
    eventSourceRef.current = es

    es.onmessage = (e) => {
      try {
        const event = JSON.parse(e.data)
        if (event.type === 'stage1_complete') {
          setStage1Data({ proposals: event.proposals, modelNames: event.model_names })
          setStage2Data(null)
          setStage3Data(null)
          setActiveTab('stage1')
        } else if (event.type === 'stage2_complete') {
          setStage2Data({ rankings: event.rankings, votes: event.votes, modelNames: event.model_names })
          setActiveTab('stage2')
        } else if (event.type === 'stage3_complete') {
          setStage3Data(event)
          setActiveTab('stage3')
        } else if (event.type === 'iteration_result') {
          // Confirmed KEEP/DISCARD from run.py — update stage3 with actual outcome
          setStage3Data(prev => prev ? { ...prev, confirmed_status: event.status } : prev)
        } else if (event.type === 'run_end') {
          setRunEnded(event)
          setStopping(false)
        }
      } catch (_) {}
    }

    return () => es.close()
  }, [])

  const keeps = results.filter(r => r.status === 'KEEP')
  const discards = results.filter(r => r.status === 'DISCARD')

  async function handleStop() {
    setStopping(true)
    try {
      await fetch(`${API}/api/stop`, { method: 'POST' })
    } catch (_) {
      setStopping(false)
    }
  }

  return (
    <div style={{ display: 'flex', height: '100vh', overflow: 'hidden' }}>
      {/* Left sidebar — stats + chart */}
      <aside style={{
        width: 260, background: '#161b2e', borderRight: '1px solid #2a2f4a',
        display: 'flex', flexDirection: 'column', padding: '20px 16px', gap: 20, overflowY: 'auto',
      }}>
        <h1 style={{ fontSize: 14, fontWeight: 700, color: '#7c8ff0', letterSpacing: 1, textTransform: 'uppercase' }}>
          Council Arena
        </h1>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          <Stat label="Iteration" value={status.iteration} />
          <Stat label="Best Score" value={`${status.best_score} / 100`} highlight />
          <Stat label="KEEPs" value={keeps.length} color="#4ade80" />
          <Stat label="DISCARDs" value={discards.length} color="#f87171" />
          <Stat label="Artifact words" value={status.artifact_words} />
        </div>

        <ResultsChart results={results} />

        <div style={{ marginTop: 'auto', display: 'flex', flexDirection: 'column', gap: 8 }}>
          {runEnded ? (
            <div style={{
              padding: '8px 10px', borderRadius: 6, fontSize: 11, lineHeight: 1.5,
              background: runEnded.reason === 'plateau' ? '#1e2a1e' : '#1e1e2a',
              border: `1px solid ${runEnded.reason === 'plateau' ? '#2d5a2d' : '#3a3a6a'}`,
              color: runEnded.reason === 'plateau' ? '#86efac' : '#a5b4fc',
            }}>
              <div style={{ fontWeight: 700, marginBottom: 2 }}>
                {runEnded.reason === 'plateau' && 'Plateau — run ended'}
                {runEnded.reason === 'stop_requested' && 'Stopped by user'}
                {runEnded.reason === 'cost_limit' && 'Cost limit reached'}
              </div>
              <div style={{ color: '#6b7280' }}>
                {runEnded.iteration} iterations · best {runEnded.best_score}/100
              </div>
            </div>
          ) : (
            <button
              onClick={handleStop}
              disabled={stopping}
              style={{
                padding: '7px 0', borderRadius: 6, border: '1px solid #5a2020',
                background: stopping ? '#1e1e1e' : '#2a1515',
                color: stopping ? '#4a5168' : '#f87171',
                fontSize: 12, fontWeight: 600, cursor: stopping ? 'default' : 'pointer',
              }}
            >
              {stopping ? 'Stopping after this iteration…' : 'Stop Run'}
            </button>
          )}
          <div style={{ fontSize: 11, color: '#4a5168' }}>
            Autoresearch × LLM Council
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        {/* Tab bar */}
        <nav style={{
          display: 'flex', gap: 4, padding: '12px 16px',
          background: '#161b2e', borderBottom: '1px solid #2a2f4a',
        }}>
          {[
            { id: 'artifact', label: 'Artifact' },
            { id: 'stage1',   label: 'Stage 1 · Proposals' },
            { id: 'stage2',   label: 'Stage 2 · Rankings' },
            { id: 'stage3',   label: 'Stage 3 · Verdict' },
          ].map(tab => (
            <button key={tab.id} onClick={() => setActiveTab(tab.id)} style={{
              padding: '6px 14px', borderRadius: 6, border: 'none', cursor: 'pointer', fontSize: 13,
              background: activeTab === tab.id ? '#7c8ff0' : '#1e2438',
              color: activeTab === tab.id ? '#fff' : '#8892b0',
              fontWeight: activeTab === tab.id ? 600 : 400,
            }}>
              {tab.label}
            </button>
          ))}
        </nav>

        {/* Tab content */}
        <div style={{ flex: 1, overflowY: 'auto', padding: 24 }}>
          {activeTab === 'artifact' && (
            <ArtifactView current={artifact} previous={prevArtifact} />
          )}
          {activeTab === 'stage1' && (
            <Stage1 proposals={stage1Data?.proposals} modelNames={stage1Data?.modelNames} />
          )}
          {activeTab === 'stage2' && (
            <Stage2 rankings={stage2Data?.rankings} votes={stage2Data?.votes} modelNames={stage2Data?.modelNames} />
          )}
          {activeTab === 'stage3' && (
            <Stage3 data={stage3Data} />
          )}
        </div>
      </main>
    </div>
  )
}

function Stat({ label, value, highlight, color }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
      <span style={{ fontSize: 12, color: '#8892b0' }}>{label}</span>
      <span style={{
        fontSize: 13, fontWeight: 600,
        color: color || (highlight ? '#fbbf24' : '#e2e8f0'),
      }}>
        {value}
      </span>
    </div>
  )
}
