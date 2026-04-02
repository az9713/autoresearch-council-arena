/**
 * ResultsChart.jsx — council_score over iterations (line chart).
 * Uses recharts, matching the tech stack of llm-council's frontend.
 */
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts'

export default function ResultsChart({ results }) {
  if (!results || results.length === 0) {
    return (
      <div style={{ height: 120, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <span style={{ fontSize: 12, color: '#4a5168' }}>No data yet</span>
      </div>
    )
  }

  const data = results
    .filter(r => r.council_score && !isNaN(parseInt(r.council_score)))
    .map((r, i) => ({
      iter: i + 1,
      score: parseInt(r.council_score),
      status: r.status,
    }))

  const CustomDot = (props) => {
    const { cx, cy, payload } = props
    if (payload.status === 'KEEP') {
      return <circle cx={cx} cy={cy} r={4} fill="#4ade80" stroke="none" />
    }
    return <circle cx={cx} cy={cy} r={2} fill="#3a3f5c" stroke="none" />
  }

  return (
    <div>
      <div style={{ fontSize: 11, color: '#4a5168', marginBottom: 8, textTransform: 'uppercase', letterSpacing: 1 }}>
        Score history
      </div>
      <ResponsiveContainer width="100%" height={120}>
        <LineChart data={data} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
          <XAxis dataKey="iter" tick={{ fontSize: 10, fill: '#4a5168' }} tickLine={false} axisLine={false} />
          <YAxis domain={[0, 100]} tick={{ fontSize: 10, fill: '#4a5168' }} tickLine={false} axisLine={false} />
          <Tooltip
            contentStyle={{ background: '#1e2438', border: '1px solid #2a2f4a', borderRadius: 6, fontSize: 12 }}
            labelStyle={{ color: '#8892b0' }}
            itemStyle={{ color: '#7c8ff0' }}
            formatter={(v, n) => [v, 'score']}
            labelFormatter={(l) => `Iter ${l}`}
          />
          <Line
            type="monotone"
            dataKey="score"
            stroke="#7c8ff0"
            strokeWidth={1.5}
            dot={<CustomDot />}
            activeDot={{ r: 5, fill: '#7c8ff0' }}
          />
        </LineChart>
      </ResponsiveContainer>
      <div style={{ display: 'flex', gap: 12, marginTop: 6 }}>
        <Legend color="#4ade80" label="KEEP" />
        <Legend color="#3a3f5c" label="DISCARD" />
      </div>
    </div>
  )
}

function Legend({ color, label }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
      <div style={{ width: 8, height: 8, borderRadius: '50%', background: color }} />
      <span style={{ fontSize: 11, color: '#4a5168' }}>{label}</span>
    </div>
  )
}
