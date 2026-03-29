import { useState, useMemo } from 'react'

const API_URL = 'https://k9s4lfemfe.execute-api.ap-south-1.amazonaws.com/prod/query'

const SCHEMA = [
  { name: 'filename',    type: 'string',  note: 'Source YAML file name' },
  { name: 'team1',       type: 'string',  note: 'First listed team' },
  { name: 'team2',       type: 'string',  note: 'Second listed team' },
  { name: 'date',        type: 'string',  note: 'Match date (YYYY-MM-DD)' },
  { name: 'winner',      type: 'string',  note: 'Winning team name (null if no result)' },
  { name: 'win_type',    type: 'string',  note: '"runs", "wickets", "super over", "bowl out"' },
  { name: 'win_margin',  type: 'bigint',  note: 'Margin of victory (runs or wickets)' },
  { name: 'method',      type: 'string',  note: '"D/L" if Duckworth-Lewis applied, else null' },
  { name: 'parsed_date', type: 'string',  note: 'YYYY-MM-DD (same as date)' },
]

const EXAMPLES = [
  {
    label: 'Most wins all-time',
    query: `SELECT winner, COUNT(*) as wins
FROM matches
GROUP BY winner
ORDER BY wins DESC
LIMIT 10`,
  },
  {
    label: 'Head-to-head records',
    query: `SELECT team1, team2, COUNT(*) as matches_played
FROM matches
GROUP BY team1, team2
ORDER BY matches_played DESC
LIMIT 10`,
  },
  {
    label: 'CSK matches',
    query: `SELECT date, team1, team2, winner, win_margin, win_type
FROM matches
WHERE winner = 'Chennai Super Kings'
ORDER BY date`,
  },
  {
    label: 'Super over wins',
    query: `SELECT winner, COUNT(*) as wins
FROM matches
WHERE win_type = 'super over'
GROUP BY winner
ORDER BY wins DESC`,
  },
  {
    label: 'D/L method matches',
    query: `SELECT date, team1, team2, winner, win_margin
FROM matches
WHERE method = 'D/L'
ORDER BY date`,
  },
  {
    label: 'Matches per season',
    query: `SELECT SUBSTR(date, 1, 4) as season, COUNT(*) as total_matches
FROM matches
GROUP BY SUBSTR(date, 1, 4)
ORDER BY season`,
  },
]

function Spinner({ size = 'sm' }) {
  const cls = size === 'lg' ? 'h-10 w-10' : 'h-4 w-4'
  return (
    <svg className={`animate-spin ${cls} text-[#e2b714]`} viewBox="0 0 24 24" fill="none">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.4 0 0 5.4 0 12h4z" />
    </svg>
  )
}

export default function App() {
  const [query, setQuery] = useState(EXAMPLES[0].query)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [schemaOpen, setSchemaOpen] = useState(false)
  const [sortCol, setSortCol] = useState(null)
  const [sortDir, setSortDir] = useState('asc')

  const runQuery = async () => {
    if (!query.trim() || loading) return
    setLoading(true)
    setError(null)
    setResult(null)
    setSortCol(null)
    try {
      const res = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query }),
      })
      const data = await res.json()
      if (data.error) {
        setError(data.error)
      } else {
        setResult(data)
      }
    } catch (e) {
      setError(`Network error: ${e.message}`)
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      e.preventDefault()
      runQuery()
    }
  }

  const handleSort = (col) => {
    if (sortCol === col) {
      setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    } else {
      setSortCol(col)
      setSortDir('asc')
    }
  }

  const sortedData = useMemo(() => {
    if (!result?.data?.length || !sortCol) return result?.data ?? []
    const idx = result.columns.indexOf(sortCol)
    return [...result.data].sort((a, b) => {
      const av = a[idx] ?? '', bv = b[idx] ?? ''
      const an = Number(av), bn = Number(bv)
      const cmp = (!isNaN(an) && av !== '' && bv !== '' && !isNaN(bn))
        ? an - bn
        : String(av).localeCompare(String(bv))
      return sortDir === 'asc' ? cmp : -cmp
    })
  }, [result, sortCol, sortDir])

  return (
    <div className="min-h-screen flex flex-col" style={{ backgroundColor: '#1a1a2e', color: '#fff' }}>

      {/* ── Header ── */}
      <header style={{ borderBottom: '1px solid rgba(226,183,20,0.2)' }} className="px-6 py-8">
        <div className="max-w-4xl mx-auto">
          <div className="flex items-center gap-3 mb-2">
            <span className="text-4xl">🏏</span>
            <h1 className="text-3xl font-bold" style={{ color: '#e2b714' }}>
              IPL Cricket Query Engine
            </h1>
          </div>
          <p style={{ color: '#9ca3af' }}>
            Run SQL queries against IPL cricket match data · 1,169 matches from 2008–2025
          </p>
        </div>
      </header>

      <main className="flex-1 px-6 py-8">
        <div className="max-w-4xl mx-auto">

          {/* ── Schema Reference ── */}
          <div
            className="mb-6 rounded-lg overflow-hidden"
            style={{ backgroundColor: '#16213e', border: '1px solid rgba(226,183,20,0.2)' }}
          >
            <button
              onClick={() => setSchemaOpen(o => !o)}
              className="w-full flex items-center justify-between px-4 py-3 text-sm font-medium transition-colors"
              style={{ color: '#e2b714' }}
              onMouseEnter={e => e.currentTarget.style.backgroundColor = 'rgba(226,183,20,0.05)'}
              onMouseLeave={e => e.currentTarget.style.backgroundColor = 'transparent'}
            >
              <span>📋 Table Schema — <code className="text-sm font-mono">matches</code></span>
              <span className="text-xs">{schemaOpen ? '▲ Hide' : '▼ Show'}</span>
            </button>
            {schemaOpen && (
              <div className="px-4 pb-4 overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr style={{ borderBottom: '1px solid #374151', color: '#6b7280' }}>
                      <th className="text-left py-2 pr-6 font-medium">Column</th>
                      <th className="text-left py-2 pr-6 font-medium">Type</th>
                      <th className="text-left py-2 font-medium">Notes</th>
                    </tr>
                  </thead>
                  <tbody>
                    {SCHEMA.map(col => (
                      <tr key={col.name} style={{ borderBottom: '1px solid rgba(55,65,81,0.5)' }}>
                        <td className="py-2 pr-6">
                          <code style={{ color: '#e2b714' }} className="font-mono text-sm">{col.name}</code>
                        </td>
                        <td className="py-2 pr-6 font-mono text-xs" style={{ color: '#6b7280' }}>{col.type}</td>
                        <td className="py-2 text-xs" style={{ color: '#6b7280' }}>{col.note}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* ── Query Editor ── */}
          <div className="mb-4">
            <textarea
              value={query}
              onChange={e => setQuery(e.target.value)}
              onKeyDown={handleKeyDown}
              rows={6}
              spellCheck={false}
              className="w-full rounded-lg px-4 py-3 font-mono text-sm resize-y transition-all"
              style={{
                backgroundColor: '#0f0f23',
                border: '1px solid rgba(226,183,20,0.3)',
                color: '#fff',
                outline: 'none',
              }}
              onFocus={e => e.target.style.borderColor = '#e2b714'}
              onBlur={e => e.target.style.borderColor = 'rgba(226,183,20,0.3)'}
              placeholder="SELECT * FROM matches LIMIT 10"
            />
            <div className="flex items-center justify-between mt-2">
              <span className="text-xs" style={{ color: '#6b7280' }}>
                Tip: <kbd className="px-1 py-0.5 rounded text-xs" style={{ backgroundColor: '#16213e', border: '1px solid #374151' }}>Ctrl</kbd> + <kbd className="px-1 py-0.5 rounded text-xs" style={{ backgroundColor: '#16213e', border: '1px solid #374151' }}>Enter</kbd> to run
              </span>
              <button
                onClick={runQuery}
                disabled={loading || !query.trim()}
                className="font-bold px-6 py-2 rounded-lg transition-all flex items-center gap-2 text-sm"
                style={{
                  backgroundColor: loading || !query.trim() ? 'rgba(226,183,20,0.4)' : '#e2b714',
                  color: '#1a1a2e',
                  cursor: loading || !query.trim() ? 'not-allowed' : 'pointer',
                }}
              >
                {loading ? (
                  <><Spinner size="sm" /><span style={{ color: '#1a1a2e' }}>Running...</span></>
                ) : (
                  <>▶ Run Query</>
                )}
              </button>
            </div>
          </div>

          {/* ── Example Queries ── */}
          <div className="mb-8">
            <p className="text-xs uppercase tracking-wider mb-3" style={{ color: '#6b7280' }}>
              Example queries
            </p>
            <div className="flex flex-wrap gap-2">
              {EXAMPLES.map(ex => (
                <button
                  key={ex.label}
                  onClick={() => { setQuery(ex.query); setError(null) }}
                  className="text-xs px-3 py-1.5 rounded-full transition-colors"
                  style={{ border: '1px solid rgba(226,183,20,0.3)', color: '#e2b714' }}
                  onMouseEnter={e => e.currentTarget.style.backgroundColor = 'rgba(226,183,20,0.1)'}
                  onMouseLeave={e => e.currentTarget.style.backgroundColor = 'transparent'}
                >
                  {ex.label}
                </button>
              ))}
            </div>
          </div>

          {/* ── Error ── */}
          {error && (
            <div
              className="mb-6 rounded-lg p-4"
              style={{ backgroundColor: 'rgba(127,29,29,0.4)', border: '1px solid rgba(239,68,68,0.4)' }}
            >
              <div className="flex items-start gap-3">
                <span className="text-lg mt-0.5">⚠️</span>
                <div>
                  <p className="font-semibold mb-1" style={{ color: '#fca5a5' }}>Query Error</p>
                  <p className="text-sm font-mono leading-relaxed" style={{ color: '#f87171' }}>{error}</p>
                </div>
              </div>
            </div>
          )}

          {/* ── Loading (full area) ── */}
          {loading && (
            <div className="flex flex-col items-center justify-center py-20" style={{ color: '#6b7280' }}>
              <Spinner size="lg" />
              <p className="mt-4 text-sm">Running query against Athena...</p>
            </div>
          )}

          {/* ── Results ── */}
          {result && !loading && (
            <div>
              <div className="flex items-center gap-3 mb-3">
                <p className="text-sm" style={{ color: '#9ca3af' }}>
                  <span className="font-semibold" style={{ color: '#fff' }}>{result.row_count.toLocaleString()}</span>
                  {' '}row{result.row_count !== 1 ? 's' : ''} returned
                </p>
                {result.message && (
                  <p className="text-sm" style={{ color: '#6b7280' }}>{result.message}</p>
                )}
              </div>

              {result.data.length === 0 ? (
                <div
                  className="text-center py-16 rounded-lg"
                  style={{ backgroundColor: '#16213e', border: '1px solid rgba(226,183,20,0.15)', color: '#6b7280' }}
                >
                  <p className="text-2xl mb-2">🏏</p>
                  <p>No results found.</p>
                </div>
              ) : (
                <div
                  className="overflow-x-auto rounded-lg"
                  style={{ border: '1px solid rgba(226,183,20,0.2)' }}
                >
                  <table className="w-full text-sm">
                    <thead style={{ backgroundColor: '#16213e' }}>
                      <tr>
                        {result.columns.map(col => (
                          <th
                            key={col}
                            onClick={() => handleSort(col)}
                            className="px-4 py-3 text-left font-medium whitespace-nowrap select-none cursor-pointer transition-colors"
                            style={{ color: '#e2b714' }}
                            onMouseEnter={e => e.currentTarget.style.backgroundColor = 'rgba(226,183,20,0.1)'}
                            onMouseLeave={e => e.currentTarget.style.backgroundColor = 'transparent'}
                          >
                            {col}
                            {sortCol === col ? (
                              <span className="ml-1 text-xs">{sortDir === 'asc' ? ' ▲' : ' ▼'}</span>
                            ) : (
                              <span className="ml-1 text-xs opacity-30">⇅</span>
                            )}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {sortedData.map((row, ri) => (
                        <tr
                          key={ri}
                          style={{
                            borderTop: '1px solid rgba(55,65,81,0.5)',
                            backgroundColor: ri % 2 === 0 ? '#0f0f23' : '#1a1a2e',
                          }}
                          onMouseEnter={e => e.currentTarget.style.backgroundColor = 'rgba(226,183,20,0.04)'}
                          onMouseLeave={e => e.currentTarget.style.backgroundColor = ri % 2 === 0 ? '#0f0f23' : '#1a1a2e'}
                        >
                          {row.map((cell, ci) => (
                            <td key={ci} className="px-4 py-2.5 whitespace-nowrap" style={{ color: '#d1d5db' }}>
                              {cell === '' || cell === null ? (
                                <span style={{ color: '#4b5563', fontStyle: 'italic' }}>null</span>
                              ) : (
                                cell
                              )}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}
        </div>
      </main>

      {/* ── Footer ── */}
      <footer
        className="px-6 py-4 text-center text-sm"
        style={{ borderTop: '1px solid rgba(226,183,20,0.15)', color: '#4b5563' }}
      >
        Built with AWS Serverless (S3, Lambda, Athena, CloudFront) ·{' '}
        <a
          href="https://github.com/jainkaadi"
          target="_blank"
          rel="noopener noreferrer"
          style={{ color: 'rgba(226,183,20,0.6)' }}
          onMouseEnter={e => e.currentTarget.style.color = '#e2b714'}
          onMouseLeave={e => e.currentTarget.style.color = 'rgba(226,183,20,0.6)'}
        >
          GitHub
        </a>
      </footer>
    </div>
  )
}
