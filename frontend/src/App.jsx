import { useState, useMemo, useEffect } from 'react'

const API_URL = 'https://k9s4lfemfe.execute-api.ap-south-1.amazonaws.com/prod/query'

const SCHEMA = [
  { name: 'filename',        type: 'string',  note: 'Source YAML file name' },
  { name: 'season',          type: 'string',  note: 'IPL season year (e.g. "2024")' },
  { name: 'match_number',    type: 'double',  note: 'Match number within the season' },
  { name: 'date',            type: 'string',  note: 'Match date (YYYY-MM-DD)' },
  { name: 'team1',           type: 'string',  note: 'First listed team' },
  { name: 'team2',           type: 'string',  note: 'Second listed team' },
  { name: 'city',            type: 'string',  note: 'City where match was played' },
  { name: 'venue',           type: 'string',  note: 'Stadium name' },
  { name: 'neutral_venue',   type: 'double',  note: '1 if neutral venue, else null' },
  { name: 'toss_winner',     type: 'string',  note: 'Team that won the toss' },
  { name: 'toss_decision',   type: 'string',  note: '"bat" or "field"' },
  { name: 'winner',          type: 'string',  note: 'Winning team name (null if no result)' },
  { name: 'win_type',        type: 'string',  note: '"runs", "wickets", "super over", "bowl out"' },
  { name: 'win_margin',      type: 'double',  note: 'Margin of victory (runs or wickets)' },
  { name: 'result',          type: 'string',  note: '"tie", "draw", "no result" (null if winner exists)' },
  { name: 'method',          type: 'string',  note: '"D/L" if Duckworth-Lewis applied, else null' },
  { name: 'eliminator',      type: 'string',  note: 'Super over winner (if applicable)' },
  { name: 'player_of_match', type: 'string',  note: 'Player of the match' },
  { name: 'umpire1',         type: 'string',  note: 'First umpire' },
  { name: 'umpire2',         type: 'string',  note: 'Second umpire' },
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
    query: `SELECT season, COUNT(*) as total_matches
FROM matches
GROUP BY season
ORDER BY season`,
  },
  {
    label: 'Player of the match leaders',
    query: `SELECT player_of_match, COUNT(*) as awards
FROM matches
WHERE player_of_match IS NOT NULL
GROUP BY player_of_match
ORDER BY awards DESC
LIMIT 10`,
  },
  {
    label: 'Toss wins by team',
    query: `SELECT toss_winner, toss_decision, COUNT(*) as tosses
FROM matches
GROUP BY toss_winner, toss_decision
ORDER BY tosses DESC
LIMIT 10`,
  },
]

function Spinner({ size = 'sm' }) {
  const cls = size === 'lg' ? 'h-8 w-8' : 'h-4 w-4'
  return (
    <svg className={`animate-spin ${cls}`} style={{ color: 'var(--ci-blue)' }} viewBox="0 0 24 24" fill="none">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.4 0 0 5.4 0 12h4z" />
    </svg>
  )
}

function SortIcon({ active, dir }) {
  if (!active) return <span className="ml-1 opacity-30 text-xs">&#8597;</span>
  return <span className="ml-1 text-xs" style={{ color: 'var(--ci-blue)' }}>{dir === 'asc' ? '▲' : '▼'}</span>
}

function PreMatch() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selectedIdx, setSelectedIdx] = useState(0)

  useEffect(() => {
    fetch('/prematch.json')
      .then(r => {
        if (!r.ok) throw new Error('No pre-match data available')
        return r.json()
      })
      .then(d => { setData(d); setLoading(false) })
      .catch(e => { setError(e.message); setLoading(false) })
  }, [])

  if (loading) return (
    <div className="flex flex-col items-center justify-center py-20 rounded-lg animate-fade-in"
      style={{ backgroundColor: 'var(--ci-surface)', border: '1px solid var(--ci-border)' }}>
      <Spinner size="lg" />
      <p className="mt-4 text-sm font-medium" style={{ color: 'var(--ci-text-muted)' }}>Loading pre-match data...</p>
    </div>
  )

  if (error || !data?.matches?.length) return (
    <div className="rounded-lg p-8 text-center animate-fade-in"
      style={{ backgroundColor: 'var(--ci-surface)', border: '1px solid var(--ci-border)' }}>
      <p className="text-sm font-medium" style={{ color: 'var(--ci-text-muted)' }}>
        {error || 'No matches scheduled for today.'}
      </p>
    </div>
  )

  const match = data.matches[selectedIdx]
  const a = match.analysis
  const h2h = a.head_to_head
  const toss = a.toss_at_venue

  const formString = (form) => form.map(f =>
    f.result === 'W'
      ? `W vs ${f.opponent.split(' ').pop()}`
      : `L vs ${f.opponent.split(' ').pop()}`
  ).join('  |  ')

  return (
    <div className="animate-fade-in" style={{ animationDelay: '0.1s' }}>
      {/* Match selector */}
      {data.matches.length > 1 && (
        <div className="mb-5">
          <select
            value={selectedIdx}
            onChange={e => setSelectedIdx(Number(e.target.value))}
            className="text-sm font-medium px-4 py-2.5 rounded-lg"
            style={{
              backgroundColor: 'var(--ci-surface)',
              border: '1px solid var(--ci-border)',
              color: 'var(--ci-text)',
              outline: 'none',
            }}
          >
            {data.matches.map((m, i) => (
              <option key={i} value={i}>
                Match {m.match_number}: {m.team1_short} vs {m.team2_short} — {m.time_ist} IST
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Match header */}
      <div className="rounded-lg mb-5 overflow-hidden"
        style={{
          background: 'linear-gradient(135deg, var(--ci-blue) 0%, var(--ci-blue-dark) 100%)',
          boxShadow: '0 2px 12px rgba(3, 152, 220, 0.25)',
        }}>
        <div className="px-6 py-5">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider"
              style={{ color: 'rgba(255,255,255,0.7)' }}>
              Match {match.match_number} &middot; IPL 2026
            </span>
            <span className="text-xs font-medium px-2.5 py-1 rounded-full"
              style={{ background: 'rgba(255,255,255,0.15)', color: 'rgba(255,255,255,0.9)' }}>
              {match.time_ist} IST
            </span>
          </div>
          <h2 className="text-xl font-bold" style={{ color: '#fff' }}>
            {match.team1} vs {match.team2}
          </h2>
          <p className="text-sm mt-1" style={{ color: 'rgba(255,255,255,0.8)' }}>
            {match.stadium} &middot; {match.city}
          </p>
        </div>
      </div>

      {/* Analysis sections */}
      <div className="space-y-4">

        {/* Head to Head */}
        <Section title="Head-to-Head Record">
          <Stat label="Total matches" value={h2h.total} />
          <Stat label={`${match.team1_short} wins`} value={h2h.team1_wins} />
          <Stat label={`${match.team2_short} wins`} value={h2h.team2_wins} />
          {h2h.no_results > 0 && <Stat label="No result" value={h2h.no_results} />}
          {h2h.last_5_encounters.length > 0 && (
            <div className="mt-3 pt-3" style={{ borderTop: '1px solid var(--ci-border-light)' }}>
              <p className="text-xs font-semibold uppercase tracking-wider mb-2"
                style={{ color: 'var(--ci-text-muted)' }}>Recent encounters</p>
              {h2h.last_5_encounters.map((e, i) => (
                <p key={i} className="text-sm mb-1" style={{ color: 'var(--ci-text-secondary)' }}>
                  {e.date} — <span style={{ color: 'var(--ci-text)', fontWeight: 500 }}>{e.winner}</span> won {e.margin} <span style={{ color: 'var(--ci-text-muted)' }}>({e.city})</span>
                </p>
              ))}
            </div>
          )}
        </Section>

        {/* Venue Record */}
        <Section title={`At ${match.city}`}>
          <Stat label={`${match.team1_short} record`}
            value={`${a.team1_venue_record.won}W / ${a.team1_venue_record.played - a.team1_venue_record.won}L in ${a.team1_venue_record.played} matches`} />
          <Stat label={`${match.team2_short} record`}
            value={`${a.team2_venue_record.won}W / ${a.team2_venue_record.played - a.team2_venue_record.won}L in ${a.team2_venue_record.played} matches`} />
          {toss.total_matches > 0 && <>
            <div className="mt-3 pt-3" style={{ borderTop: '1px solid var(--ci-border-light)' }}>
              <Stat label="Bat first wins" value={toss.bat_first_won} />
              <Stat label="Field first wins" value={toss.field_first_won} />
            </div>
          </>}
        </Section>

        {/* Toss Factor */}
        <Section title="Toss Factor at Venue">
          <Stat label="Chose to field" value={`${toss.chose_field_pct}%`} />
          <Stat label="Toss winner won match" value={`${toss.toss_winner_won_pct}%`} />
        </Section>

        {/* Recent Form */}
        <Section title="Recent Form (Last 5)">
          <p className="text-xs font-semibold uppercase tracking-wider mb-1.5"
            style={{ color: 'var(--ci-text-muted)' }}>{match.team1_short}</p>
          <div className="flex gap-1.5 mb-3 flex-wrap">
            {a.team1_recent_form.map((f, i) => (
              <span key={i} className="text-xs font-medium px-2 py-1 rounded"
                style={{
                  backgroundColor: f.result === 'W' ? '#DEF7EC' : '#FDE8E8',
                  color: f.result === 'W' ? '#03543F' : '#9B1C1C',
                }}>
                {f.result} vs {f.opponent.split(' ').pop()}
              </span>
            ))}
          </div>
          <p className="text-xs font-semibold uppercase tracking-wider mb-1.5"
            style={{ color: 'var(--ci-text-muted)' }}>{match.team2_short}</p>
          <div className="flex gap-1.5 flex-wrap">
            {a.team2_recent_form.map((f, i) => (
              <span key={i} className="text-xs font-medium px-2 py-1 rounded"
                style={{
                  backgroundColor: f.result === 'W' ? '#DEF7EC' : '#FDE8E8',
                  color: f.result === 'W' ? '#03543F' : '#9B1C1C',
                }}>
                {f.result} vs {f.opponent.split(' ').pop()}
              </span>
            ))}
          </div>
        </Section>
      </div>

      {/* Generated timestamp */}
      <p className="text-xs mt-5 text-center" style={{ color: 'var(--ci-text-muted)' }}>
        Last updated: {new Date(data.generated_at).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' })}
      </p>
    </div>
  )
}

function Section({ title, children }) {
  return (
    <div className="rounded-lg px-5 py-4"
      style={{ backgroundColor: 'var(--ci-surface)', border: '1px solid var(--ci-border)' }}>
      <h3 className="text-sm font-bold mb-3" style={{ color: 'var(--ci-text)' }}>{title}</h3>
      {children}
    </div>
  )
}

function Stat({ label, value }) {
  return (
    <div className="flex items-center justify-between py-1">
      <span className="text-sm" style={{ color: 'var(--ci-text-secondary)' }}>{label}</span>
      <span className="text-sm font-semibold" style={{ color: 'var(--ci-text)' }}>{value}</span>
    </div>
  )
}

async function athenaQuery(sql) {
  const res = await fetch(API_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query: sql }),
  })
  const data = await res.json()
  if (data.error) throw new Error(data.error)
  // Convert array-of-arrays + columns into array-of-objects
  return data.columns
    ? data.data.map(row =>
        Object.fromEntries(data.columns.map((c, i) => [c, row[i]]))
      )
    : data
}

function formatDismissal(dismissalKind, bowler, fielder) {
  if (!dismissalKind) return 'not out'
  switch (dismissalKind) {
    case 'caught': return fielder ? `c ${fielder} b ${bowler}` : `c&b ${bowler}`
    case 'bowled': return `b ${bowler}`
    case 'lbw': return `lbw b ${bowler}`
    case 'stumped': return `st ${fielder} b ${bowler}`
    case 'run out': return fielder ? `run out (${fielder})` : 'run out'
    case 'caught and bowled': return `c&b ${bowler}`
    case 'hit wicket': return `hit wkt b ${bowler}`
    case 'retired hurt': return 'retired hurt'
    case 'obstructing the field': return 'obstructing'
    default: return dismissalKind
  }
}

function computeScorecard(rows) {
  const innings = {}

  for (const r of rows) {
    const inn = r.innings
    if (!innings[inn]) {
      innings[inn] = {
        innings: inn,
        batting_team: r.batting_team,
        bowling_team: r.bowling_team,
        batters: {},
        bowlers: {},
        extras: { wides: 0, noballs: 0, byes: 0, legbyes: 0 },
        total_runs: 0,
        total_wickets: 0,
        last_over: 0,
        last_ball: 0,
      }
    }
    const inn_data = innings[inn]

    // Innings totals
    inn_data.total_runs += Number(r.total_runs) || 0
    if (Number(r.is_wicket) === 1) inn_data.total_wickets += 1
    inn_data.last_over = Math.max(inn_data.last_over, Number(r.over) || 0)
    inn_data.last_ball = Number(r.ball) || 0

    // Extras
    inn_data.extras.wides += Number(r.wides) || 0
    inn_data.extras.noballs += Number(r.noballs) || 0
    inn_data.extras.byes += Number(r.byes) || 0
    inn_data.extras.legbyes += Number(r.legbyes) || 0

    // Batter stats (skip wide deliveries for ball count)
    const batter = r.batter
    if (!inn_data.batters[batter]) {
      inn_data.batters[batter] = { name: batter, runs: 0, balls: 0, fours: 0, sixes: 0, dismissal: null, order: Object.keys(inn_data.batters).length }
    }
    const b = inn_data.batters[batter]
    b.runs += Number(r.batter_runs) || 0
    if (!Number(r.wides)) b.balls += 1
    if (Number(r.batter_runs) === 4) b.fours += 1
    if (Number(r.batter_runs) === 6) b.sixes += 1

    // Dismissal
    if (Number(r.is_wicket) === 1 && r.player_out) {
      const dismissed = r.player_out
      if (!inn_data.batters[dismissed]) {
        inn_data.batters[dismissed] = { name: dismissed, runs: 0, balls: 0, fours: 0, sixes: 0, dismissal: null, order: Object.keys(inn_data.batters).length }
      }
      inn_data.batters[dismissed].dismissal = formatDismissal(r.dismissal_kind, r.bowler, r.fielder)
    }

    // Bowler stats (skip no-balls and wides for legal delivery count)
    const bowler = r.bowler
    if (!inn_data.bowlers[bowler]) {
      inn_data.bowlers[bowler] = { name: bowler, runs: 0, balls: 0, wickets: 0, wides: 0, noballs: 0, maiden_overs: new Set(), over_runs: {} }
    }
    const bwl = inn_data.bowlers[bowler]
    bwl.runs += Number(r.total_runs) || 0
    if (!Number(r.wides) && !Number(r.noballs)) {
      bwl.balls += 1
    }
    bwl.wides += Number(r.wides) || 0
    bwl.noballs += Number(r.noballs) || 0

    // Track runs per over for maiden detection
    const overKey = `${r.over}`
    if (!bwl.over_runs[overKey]) bwl.over_runs[overKey] = { runs: 0, hasExtra: false }
    bwl.over_runs[overKey].runs += Number(r.total_runs) || 0
    if (Number(r.wides) || Number(r.noballs)) bwl.over_runs[overKey].hasExtra = true

    // Wickets (not run out, retired hurt, obstructing)
    const nonBowlerDismissals = ['run out', 'retired hurt', 'obstructing the field']
    if (Number(r.is_wicket) === 1 && !nonBowlerDismissals.includes(r.dismissal_kind)) {
      bwl.wickets += 1
    }
  }

  return Object.values(innings).map(inn => {
    // Compute overs string
    const lastOver = inn.last_over
    const lastBall = inn.last_ball
    const oversStr = lastBall === 0 ? `${lastOver}.0` : `${lastOver}.${lastBall}`

    // Compute maiden overs for each bowler
    const batters = Object.values(inn.batters).sort((a, b) => a.order - b.order)
    const bowlers = Object.values(inn.bowlers).map(bwl => {
      const maidens = Object.values(bwl.over_runs).filter(o => o.runs === 0 && !o.hasExtra).length
      const overs = `${Math.floor(bwl.balls / 6)}.${bwl.balls % 6}`
      const economy = bwl.balls > 0 ? (bwl.runs / (bwl.balls / 6)).toFixed(2) : '-'
      return { ...bwl, overs, maidens, economy }
    })

    const totalExtras = inn.extras.wides + inn.extras.noballs + inn.extras.byes + inn.extras.legbyes

    return {
      innings: inn.innings,
      batting_team: inn.batting_team,
      bowling_team: inn.bowling_team,
      batters,
      bowlers,
      extras: inn.extras,
      total_runs: inn.total_runs,
      total_wickets: inn.total_wickets,
      overs: oversStr,
      total_extras: totalExtras,
    }
  })
}

function InningsBatting({ batters }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr style={{ borderBottom: '2px solid var(--ci-blue)' }}>
            {['Batter', 'Dismissal', 'R', 'B', '4s', '6s', 'SR'].map(h => (
              <th key={h} className={`py-2 text-xs font-semibold uppercase tracking-wider ${h === 'Batter' || h === 'Dismissal' ? 'text-left pr-4' : 'text-right px-2'}`}
                style={{ color: 'var(--ci-text-muted)' }}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {batters.map((b, i) => {
            const sr = b.balls > 0 ? (b.runs / b.balls * 100).toFixed(1) : '-'
            const notOut = !b.dismissal
            return (
              <tr key={b.name} style={{
                borderBottom: '1px solid var(--ci-border-light)',
                backgroundColor: i % 2 === 0 ? 'transparent' : 'var(--ci-surface-alt)',
              }}>
                <td className="py-2 pr-4 font-medium whitespace-nowrap" style={{ color: 'var(--ci-text)' }}>
                  {b.name}{notOut && <span className="ml-1 text-xs" style={{ color: 'var(--ci-text-muted)' }}>*</span>}
                </td>
                <td className="py-2 pr-4 text-xs whitespace-nowrap" style={{ color: 'var(--ci-text-secondary)' }}>
                  {notOut ? 'not out' : b.dismissal}
                </td>
                <td className="py-2 px-2 text-right font-semibold whitespace-nowrap" style={{ color: 'var(--ci-text)' }}>{b.runs}</td>
                <td className="py-2 px-2 text-right whitespace-nowrap" style={{ color: 'var(--ci-text-secondary)' }}>{b.balls}</td>
                <td className="py-2 px-2 text-right whitespace-nowrap" style={{ color: 'var(--ci-text-secondary)' }}>{b.fours}</td>
                <td className="py-2 px-2 text-right whitespace-nowrap" style={{ color: 'var(--ci-text-secondary)' }}>{b.sixes}</td>
                <td className="py-2 px-2 text-right whitespace-nowrap" style={{ color: 'var(--ci-text-muted)' }}>{sr}</td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

function InningsBowling({ bowlers }) {
  return (
    <div className="overflow-x-auto mt-4">
      <table className="w-full text-sm">
        <thead>
          <tr style={{ borderBottom: '1px solid var(--ci-border)' }}>
            {['Bowler', 'O', 'M', 'R', 'W', 'Econ', 'Wd', 'Nb'].map(h => (
              <th key={h} className={`py-2 text-xs font-semibold uppercase tracking-wider ${h === 'Bowler' ? 'text-left pr-4' : 'text-right px-2'}`}
                style={{ color: 'var(--ci-text-muted)' }}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {bowlers.map((b, i) => (
            <tr key={b.name} style={{
              borderBottom: '1px solid var(--ci-border-light)',
              backgroundColor: i % 2 === 0 ? 'transparent' : 'var(--ci-surface-alt)',
            }}>
              <td className="py-2 pr-4 font-medium whitespace-nowrap" style={{ color: 'var(--ci-text)' }}>{b.name}</td>
              <td className="py-2 px-2 text-right whitespace-nowrap" style={{ color: 'var(--ci-text-secondary)' }}>{b.overs}</td>
              <td className="py-2 px-2 text-right whitespace-nowrap" style={{ color: 'var(--ci-text-secondary)' }}>{b.maidens}</td>
              <td className="py-2 px-2 text-right whitespace-nowrap" style={{ color: 'var(--ci-text-secondary)' }}>{b.runs}</td>
              <td className="py-2 px-2 text-right font-semibold whitespace-nowrap" style={{ color: b.wickets >= 3 ? 'var(--ci-blue)' : 'var(--ci-text)' }}>{b.wickets}</td>
              <td className="py-2 px-2 text-right whitespace-nowrap" style={{ color: 'var(--ci-text-muted)' }}>{b.economy}</td>
              <td className="py-2 px-2 text-right whitespace-nowrap" style={{ color: 'var(--ci-text-muted)' }}>{b.wides || '-'}</td>
              <td className="py-2 px-2 text-right whitespace-nowrap" style={{ color: 'var(--ci-text-muted)' }}>{b.noballs || '-'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function LatestMatch() {
  const [match, setMatch] = useState(null)
  const [scorecard, setScorecard] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [status, setStatus] = useState('Fetching latest match...')

  useEffect(() => {
    let cancelled = false
    async function load() {
      try {
        setStatus('Fetching latest match...')
        const matchRows = await athenaQuery(`
          SELECT filename, date, team1, team2, city, venue,
                 toss_winner, toss_decision, winner, win_type,
                 win_margin, result, method, player_of_match
          FROM matches
          ORDER BY date DESC
          LIMIT 1
        `)
        if (cancelled) return
        if (!matchRows.length) throw new Error('No match data found')
        const m = matchRows[0]
        setMatch(m)

        const matchId = parseInt(m.filename.replace('.yaml', '').replace('.json', ''))
        if (isNaN(matchId)) throw new Error(`Could not parse match_id from filename: ${m.filename}`)

        setStatus('Loading scorecard...')
        const deliveries = await athenaQuery(`
          SELECT innings, batting_team, bowling_team, over, ball,
                 batter, bowler, batter_runs, extras_total, total_runs,
                 wides, noballs, byes, legbyes, is_wicket,
                 player_out, dismissal_kind, fielder
          FROM deliveries
          WHERE match_id = ${matchId}
          ORDER BY innings, over, ball
          LIMIT 400
        `)
        if (cancelled) return
        if (!deliveries.length) throw new Error('No delivery data found for this match')
        setScorecard(computeScorecard(deliveries))
      } catch (e) {
        if (!cancelled) setError(e.message)
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    load()
    return () => { cancelled = true }
  }, [])

  if (loading) return (
    <div className="flex flex-col items-center justify-center py-20 rounded-lg animate-fade-in"
      style={{ backgroundColor: 'var(--ci-surface)', border: '1px solid var(--ci-border)' }}>
      <Spinner size="lg" />
      <p className="mt-4 text-sm font-medium" style={{ color: 'var(--ci-text-muted)' }}>{status}</p>
    </div>
  )

  if (error) return (
    <div className="rounded-lg p-8 text-center animate-fade-in"
      style={{ backgroundColor: 'var(--ci-surface)', border: '1px solid var(--ci-border)' }}>
      <p className="text-sm font-medium" style={{ color: 'var(--ci-text-muted)' }}>Error: {error}</p>
    </div>
  )

  const resultLine = match.winner
    ? `${match.winner} won by ${parseInt(match.win_margin)} ${match.win_type}${match.method ? ` (${match.method})` : ''}`
    : match.result || 'No result'

  return (
    <div className="animate-fade-in" style={{ animationDelay: '0.1s' }}>
      {/* Match header */}
      <div className="rounded-lg mb-5 overflow-hidden"
        style={{
          background: 'linear-gradient(135deg, var(--ci-blue) 0%, var(--ci-blue-dark) 100%)',
          boxShadow: '0 2px 12px rgba(3, 152, 220, 0.25)',
        }}>
        <div className="px-6 py-5">
          <span className="text-xs font-semibold uppercase tracking-wider"
            style={{ color: 'rgba(255,255,255,0.7)' }}>
            {match.date}
          </span>
          <h2 className="text-xl font-bold mt-1" style={{ color: '#fff' }}>
            {match.team1} vs {match.team2}
          </h2>
          <p className="text-sm mt-1" style={{ color: 'rgba(255,255,255,0.8)' }}>
            {match.venue}{match.city ? ` \u00b7 ${match.city}` : ''}
          </p>
          <p className="text-sm mt-2 font-semibold" style={{ color: 'rgba(255,255,255,0.95)' }}>
            {resultLine}
          </p>
        </div>
      </div>

      {/* Innings */}
      {scorecard.map((inn, i) => (
        <div key={inn.innings} className="rounded-lg mb-4 overflow-hidden"
          style={{ backgroundColor: 'var(--ci-surface)', border: '1px solid var(--ci-border)' }}>
          {/* Innings header */}
          <div className="px-5 py-3 flex items-center justify-between"
            style={{ borderBottom: '1px solid var(--ci-border)', backgroundColor: 'var(--ci-surface-alt)' }}>
            <span className="text-sm font-bold" style={{ color: 'var(--ci-text)' }}>
              {inn.batting_team} — {i === 0 ? '1st' : '2nd'} Innings
            </span>
            <span className="text-sm font-semibold" style={{ color: 'var(--ci-blue)' }}>
              {inn.total_runs}/{inn.total_wickets} ({inn.overs} ov)
            </span>
          </div>
          <div className="px-5 py-4">
            <InningsBatting batters={inn.batters} />
            {/* Extras + Total */}
            <div className="mt-2 pt-2 flex justify-between text-sm"
              style={{ borderTop: '1px solid var(--ci-border-light)' }}>
              <span style={{ color: 'var(--ci-text-secondary)' }}>
                Extras: {inn.total_extras}
                <span className="ml-2 text-xs" style={{ color: 'var(--ci-text-muted)' }}>
                  (w {inn.extras.wides}, nb {inn.extras.noballs}, b {inn.extras.byes}, lb {inn.extras.legbyes})
                </span>
              </span>
              <span className="font-bold" style={{ color: 'var(--ci-text)' }}>
                Total: {inn.total_runs}/{inn.total_wickets} ({inn.overs} ov)
              </span>
            </div>
            <InningsBowling bowlers={inn.bowlers} />
          </div>
        </div>
      ))}

      {/* Match summary */}
      <div className="rounded-lg px-5 py-4"
        style={{ backgroundColor: 'var(--ci-surface)', border: '1px solid var(--ci-border)' }}>
        <h3 className="text-sm font-bold mb-3" style={{ color: 'var(--ci-text)' }}>Match Summary</h3>
        {match.player_of_match && <Stat label="Player of the Match" value={match.player_of_match} />}
        <Stat label="Toss" value={`${match.toss_winner} chose to ${match.toss_decision}`} />
        {match.venue && <Stat label="Venue" value={match.venue} />}
      </div>
    </div>
  )
}

export default function App() {
  const [activeTab, setActiveTab] = useState('prematch')
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
    <div className="min-h-screen flex flex-col" style={{ backgroundColor: 'var(--ci-bg)' }}>

      {/* ── Top Nav Bar ── */}
      <nav
        className="animate-fade-in"
        style={{
          background: 'linear-gradient(135deg, var(--ci-blue) 0%, var(--ci-blue-dark) 100%)',
          boxShadow: '0 2px 8px rgba(3, 152, 220, 0.25)',
        }}
      >
        <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            {/* Cricket ball icon */}
            <div
              className="flex items-center justify-center rounded-full"
              style={{
                width: 36, height: 36,
                background: 'rgba(255,255,255,0.15)',
                backdropFilter: 'blur(4px)',
              }}
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round">
                <circle cx="12" cy="12" r="10" />
                <path d="M8 4.5c1.5 2 1.5 4 0 6s-1.5 4 0 6" />
                <path d="M16 4.5c-1.5 2-1.5 4 0 6s1.5 4 0 6" />
              </svg>
            </div>
            <div>
              <h1 className="text-lg font-bold tracking-tight" style={{ color: '#fff', letterSpacing: '-0.02em' }}>
                IPL Query Engine
              </h1>
            </div>
          </div>
          <div className="hidden sm:flex items-center gap-2">
            <span
              className="text-xs font-medium px-2.5 py-1 rounded-full"
              style={{
                background: 'rgba(255,255,255,0.15)',
                color: 'rgba(255,255,255,0.9)',
                backdropFilter: 'blur(4px)',
              }}
            >
              1,169 matches
            </span>
            <span
              className="text-xs font-medium px-2.5 py-1 rounded-full"
              style={{
                background: 'rgba(255,255,255,0.15)',
                color: 'rgba(255,255,255,0.9)',
              }}
            >
              2008 &ndash; 2025
            </span>
          </div>
        </div>
      </nav>

      {/* ── Tab Navigation ── */}
      <div
        style={{
          backgroundColor: 'var(--ci-surface)',
          borderBottom: '1px solid var(--ci-border)',
        }}
      >
        <div className="max-w-5xl mx-auto px-6 flex gap-0">
          {[
            { id: 'prematch', label: "Today's Match" },
            { id: 'latest', label: 'Latest Match' },
            { id: 'query', label: 'Query Engine' },
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className="px-4 py-3 text-sm font-medium transition-colors relative"
              style={{
                color: activeTab === tab.id ? 'var(--ci-blue)' : 'var(--ci-text-muted)',
                background: 'none',
                border: 'none',
                cursor: 'pointer',
              }}
            >
              {tab.label}
              {activeTab === tab.id && (
                <span className="absolute bottom-0 left-0 right-0 h-0.5"
                  style={{ backgroundColor: 'var(--ci-blue)' }} />
              )}
            </button>
          ))}
        </div>
      </div>

      <main className="flex-1 px-6 py-6 animate-fade-in" style={{ animationDelay: '0.1s' }}>
        <div className="max-w-5xl mx-auto">

          {activeTab === 'prematch' && <PreMatch />}

          {activeTab === 'latest' && <LatestMatch />}

          {activeTab === 'query' && <>

          {/* ── Schema Reference ── */}
          <div
            className="mb-5 rounded-lg overflow-hidden transition-shadow"
            style={{
              backgroundColor: 'var(--ci-surface)',
              border: '1px solid var(--ci-border)',
              boxShadow: schemaOpen ? '0 2px 12px rgba(0,0,0,0.06)' : 'none',
            }}
          >
            <button
              onClick={() => setSchemaOpen(o => !o)}
              className="w-full flex items-center justify-between px-5 py-3 text-sm font-semibold transition-colors"
              style={{ color: 'var(--ci-text)' }}
              onMouseEnter={e => e.currentTarget.style.backgroundColor = 'var(--ci-highlight)'}
              onMouseLeave={e => e.currentTarget.style.backgroundColor = 'transparent'}
            >
              <span className="flex items-center gap-2">
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="var(--ci-blue)" strokeWidth="1.5">
                  <rect x="2" y="2" width="12" height="12" rx="2" />
                  <line x1="2" y1="6" x2="14" y2="6" />
                  <line x1="6" y1="6" x2="6" y2="14" />
                </svg>
                <span>Table: <code className="font-mono text-xs px-1.5 py-0.5 rounded" style={{ backgroundColor: 'var(--ci-bg)', color: 'var(--ci-blue)' }}>matches</code></span>
              </span>
              <span
                className="text-xs px-2 py-0.5 rounded"
                style={{ backgroundColor: 'var(--ci-bg)', color: 'var(--ci-text-muted)' }}
              >
                {schemaOpen ? 'Hide' : 'Show'} {SCHEMA.length} columns
              </span>
            </button>
            {schemaOpen && (
              <div className="px-5 pb-4 overflow-x-auto animate-slide-down">
                <table className="w-full text-sm">
                  <thead>
                    <tr style={{ borderBottom: '2px solid var(--ci-blue)' }}>
                      <th className="text-left py-2 pr-6 font-semibold text-xs uppercase tracking-wider" style={{ color: 'var(--ci-text-muted)' }}>Column</th>
                      <th className="text-left py-2 pr-6 font-semibold text-xs uppercase tracking-wider" style={{ color: 'var(--ci-text-muted)' }}>Type</th>
                      <th className="text-left py-2 font-semibold text-xs uppercase tracking-wider" style={{ color: 'var(--ci-text-muted)' }}>Description</th>
                    </tr>
                  </thead>
                  <tbody>
                    {SCHEMA.map((col, i) => (
                      <tr
                        key={col.name}
                        style={{
                          borderBottom: '1px solid var(--ci-border-light)',
                          backgroundColor: i % 2 === 0 ? 'transparent' : 'var(--ci-surface-alt)',
                        }}
                      >
                        <td className="py-2 pr-6">
                          <code className="font-mono text-xs font-medium" style={{ color: 'var(--ci-blue-deeper)' }}>{col.name}</code>
                        </td>
                        <td className="py-2 pr-6 font-mono text-xs" style={{ color: 'var(--ci-text-muted)' }}>{col.type}</td>
                        <td className="py-2 text-xs" style={{ color: 'var(--ci-text-secondary)' }}>{col.note}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* ── Query Editor Card ── */}
          <div
            className="mb-5 rounded-lg overflow-hidden"
            style={{
              backgroundColor: 'var(--ci-surface)',
              border: '1px solid var(--ci-border)',
              boxShadow: '0 1px 4px rgba(0,0,0,0.04)',
            }}
          >
            {/* Card header */}
            <div
              className="px-5 py-3 flex items-center justify-between"
              style={{ borderBottom: '1px solid var(--ci-border-light)' }}
            >
              <span className="text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--ci-text-muted)' }}>
                SQL Query
              </span>
              <span className="text-xs" style={{ color: 'var(--ci-text-muted)' }}>
                <kbd className="px-1.5 py-0.5 rounded text-xs font-mono" style={{ backgroundColor: 'var(--ci-bg)', border: '1px solid var(--ci-border)' }}>
                  {navigator.platform?.includes('Mac') ? 'Cmd' : 'Ctrl'}
                </kbd>
                {' + '}
                <kbd className="px-1.5 py-0.5 rounded text-xs font-mono" style={{ backgroundColor: 'var(--ci-bg)', border: '1px solid var(--ci-border)' }}>
                  Enter
                </kbd>
                {' to run'}
              </span>
            </div>

            {/* Editor area */}
            <textarea
              value={query}
              onChange={e => setQuery(e.target.value)}
              onKeyDown={handleKeyDown}
              rows={6}
              spellCheck={false}
              className="w-full px-5 py-4 text-sm resize-y"
              style={{
                backgroundColor: '#FAFBFC',
                color: 'var(--ci-text)',
                outline: 'none',
                border: 'none',
                borderBottom: '1px solid var(--ci-border-light)',
                lineHeight: 1.7,
              }}
              placeholder="SELECT * FROM matches LIMIT 10"
            />

            {/* Actions row */}
            <div className="px-5 py-3 flex items-center justify-between">
              <div className="flex flex-wrap gap-1.5">
                {EXAMPLES.map(ex => (
                  <button
                    key={ex.label}
                    onClick={() => { setQuery(ex.query); setError(null) }}
                    className="text-xs px-2.5 py-1 rounded-md transition-all font-medium"
                    style={{
                      backgroundColor: 'var(--ci-bg)',
                      color: 'var(--ci-text-secondary)',
                      border: '1px solid var(--ci-border)',
                    }}
                    onMouseEnter={e => {
                      e.currentTarget.style.backgroundColor = 'var(--ci-highlight)'
                      e.currentTarget.style.borderColor = 'var(--ci-blue)'
                      e.currentTarget.style.color = 'var(--ci-blue)'
                    }}
                    onMouseLeave={e => {
                      e.currentTarget.style.backgroundColor = 'var(--ci-bg)'
                      e.currentTarget.style.borderColor = 'var(--ci-border)'
                      e.currentTarget.style.color = 'var(--ci-text-secondary)'
                    }}
                  >
                    {ex.label}
                  </button>
                ))}
              </div>
              <button
                onClick={runQuery}
                disabled={loading || !query.trim()}
                className="font-semibold px-5 py-2 rounded-lg transition-all flex items-center gap-2 text-sm ml-4 shrink-0"
                style={{
                  background: loading || !query.trim()
                    ? 'var(--ci-border)'
                    : 'linear-gradient(135deg, var(--ci-blue) 0%, var(--ci-blue-dark) 100%)',
                  color: loading || !query.trim() ? 'var(--ci-text-muted)' : '#fff',
                  cursor: loading || !query.trim() ? 'not-allowed' : 'pointer',
                  boxShadow: loading || !query.trim() ? 'none' : '0 2px 8px rgba(3, 152, 220, 0.3)',
                }}
              >
                {loading ? (
                  <><Spinner size="sm" /><span>Running...</span></>
                ) : (
                  <>
                    <svg width="14" height="14" viewBox="0 0 14 14" fill="currentColor">
                      <path d="M3 1.5v11l9-5.5z" />
                    </svg>
                    Run Query
                  </>
                )}
              </button>
            </div>
          </div>

          {/* ── Error ── */}
          {error && (
            <div
              className="mb-5 rounded-lg p-4 animate-fade-in"
              style={{
                backgroundColor: '#FEF2F2',
                border: '1px solid #FECACA',
              }}
            >
              <div className="flex items-start gap-3">
                <div
                  className="flex items-center justify-center rounded-full shrink-0"
                  style={{ width: 28, height: 28, backgroundColor: '#FEE2E2' }}
                >
                  <svg width="14" height="14" viewBox="0 0 14 14" fill="var(--ci-red)">
                    <path d="M7 0a7 7 0 100 14A7 7 0 007 0zm0 10.5a.875.875 0 110-1.75.875.875 0 010 1.75zM7.875 7a.875.875 0 01-1.75 0V3.5a.875.875 0 011.75 0V7z" />
                  </svg>
                </div>
                <div>
                  <p className="font-semibold text-sm mb-1" style={{ color: '#991B1B' }}>Query Error</p>
                  <p className="text-sm font-mono leading-relaxed" style={{ color: '#B91C1C' }}>{error}</p>
                </div>
              </div>
            </div>
          )}

          {/* ── Loading ── */}
          {loading && (
            <div
              className="flex flex-col items-center justify-center py-20 rounded-lg animate-fade-in"
              style={{
                backgroundColor: 'var(--ci-surface)',
                border: '1px solid var(--ci-border)',
              }}
            >
              <Spinner size="lg" />
              <p className="mt-4 text-sm font-medium" style={{ color: 'var(--ci-text-muted)' }}>
                Querying Athena...
              </p>
            </div>
          )}

          {/* ── Results ── */}
          {result && !loading && (
            <div className="animate-fade-in" style={{ animationDelay: '0.05s' }}>
              {/* Results header bar */}
              <div
                className="flex items-center gap-3 mb-3 px-1"
              >
                <div
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-md"
                  style={{ backgroundColor: 'var(--ci-surface)', border: '1px solid var(--ci-border)' }}
                >
                  <span className="font-bold text-sm" style={{ color: 'var(--ci-blue)' }}>
                    {result.row_count.toLocaleString()}
                  </span>
                  <span className="text-xs" style={{ color: 'var(--ci-text-muted)' }}>
                    row{result.row_count !== 1 ? 's' : ''}
                  </span>
                </div>
                {result.message && (
                  <p className="text-xs" style={{ color: 'var(--ci-text-muted)' }}>{result.message}</p>
                )}
              </div>

              {result.data.length === 0 ? (
                <div
                  className="text-center py-16 rounded-lg"
                  style={{
                    backgroundColor: 'var(--ci-surface)',
                    border: '1px solid var(--ci-border)',
                    color: 'var(--ci-text-muted)',
                  }}
                >
                  <svg className="mx-auto mb-3" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="var(--ci-text-muted)" strokeWidth="1.5">
                    <circle cx="12" cy="12" r="10" />
                    <path d="M8 4.5c1.5 2 1.5 4 0 6s-1.5 4 0 6" />
                    <path d="M16 4.5c-1.5 2-1.5 4 0 6s1.5 4 0 6" />
                  </svg>
                  <p className="font-medium">No results found</p>
                </div>
              ) : (
                <div
                  className="overflow-x-auto rounded-lg"
                  style={{
                    border: '1px solid var(--ci-border)',
                    boxShadow: '0 1px 4px rgba(0,0,0,0.04)',
                  }}
                >
                  <table className="w-full text-sm" style={{ backgroundColor: 'var(--ci-surface)' }}>
                    <thead>
                      <tr style={{ borderBottom: '2px solid var(--ci-blue)' }}>
                        {result.columns.map(col => (
                          <th
                            key={col}
                            onClick={() => handleSort(col)}
                            className="px-4 py-3 text-left font-semibold whitespace-nowrap select-none cursor-pointer transition-colors text-xs uppercase tracking-wider"
                            style={{
                              color: sortCol === col ? 'var(--ci-blue)' : 'var(--ci-text-secondary)',
                              backgroundColor: 'var(--ci-surface-alt)',
                            }}
                            onMouseEnter={e => e.currentTarget.style.backgroundColor = 'var(--ci-highlight)'}
                            onMouseLeave={e => e.currentTarget.style.backgroundColor = 'var(--ci-surface-alt)'}
                          >
                            {col}
                            <SortIcon active={sortCol === col} dir={sortDir} />
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {sortedData.map((row, ri) => (
                        <tr
                          key={ri}
                          style={{
                            borderTop: '1px solid var(--ci-border-light)',
                            backgroundColor: ri % 2 === 0 ? 'var(--ci-surface)' : 'var(--ci-surface-alt)',
                          }}
                          onMouseEnter={e => e.currentTarget.style.backgroundColor = 'var(--ci-highlight)'}
                          onMouseLeave={e => e.currentTarget.style.backgroundColor = ri % 2 === 0 ? 'var(--ci-surface)' : 'var(--ci-surface-alt)'}
                        >
                          {row.map((cell, ci) => (
                            <td key={ci} className="px-4 py-2.5 whitespace-nowrap" style={{ color: 'var(--ci-text)' }}>
                              {cell === '' || cell === null ? (
                                <span className="italic text-xs" style={{ color: 'var(--ci-text-muted)' }}>null</span>
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
          </>}
        </div>
      </main>

      {/* ── Footer ── */}
      <footer
        className="px-6 py-4 text-center text-xs"
        style={{
          borderTop: '1px solid var(--ci-border)',
          backgroundColor: 'var(--ci-surface)',
          color: 'var(--ci-text-muted)',
        }}
      >
        Built with AWS Serverless (S3, Lambda, Athena, CloudFront) &middot;{' '}
        <a
          href="https://github.com/jainkaadi"
          target="_blank"
          rel="noopener noreferrer"
          className="font-medium transition-colors"
          style={{ color: 'var(--ci-blue)' }}
          onMouseEnter={e => e.currentTarget.style.color = 'var(--ci-blue-dark)'}
          onMouseLeave={e => e.currentTarget.style.color = 'var(--ci-blue)'}
        >
          GitHub
        </a>
      </footer>
    </div>
  )
}
