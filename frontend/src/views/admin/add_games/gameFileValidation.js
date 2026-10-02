export const GAME_COLUMNS = [
  'date',
  'home_team',
  'away_team',
  'home_score',
  'away_score',
  'neutral_site',
]

const cleanTeamName = (value) => String(value ?? '').trim().replace(/\s+/g, ' ')

const normalizedDate = (value) => {
  const candidate = String(value ?? '').trim()
  let year
  let month
  let day

  if (/^\d{4}-\d{2}-\d{2}$/.test(candidate)) {
    ;[year, month, day] = candidate.split('-').map(Number)
  } else if (/^\d{2}\/\d{2}\/\d{4}$/.test(candidate)) {
    const parts = candidate.split('/').map(Number)
    ;[month, day, year] = parts
  } else {
    return null
  }

  const parsed = new Date(Date.UTC(year, month - 1, day))
  if (
    parsed.getUTCFullYear() !== year
    || parsed.getUTCMonth() !== month - 1
    || parsed.getUTCDate() !== day
  ) {
    return null
  }
  return `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`
}

const gameKey = (date, homeTeam, awayTeam) => [
  normalizedDate(date),
  ...[cleanTeamName(homeTeam).toLowerCase(), cleanTeamName(awayTeam).toLowerCase()].sort(),
].join('|')

export const validateGameRows = (rows) => {
  const errors = []
  const games = []
  const identities = new Map()

  if (!rows.length) {
    return { games, errors: ['Game file does not contain any games.'] }
  }

  rows.forEach((row, index) => {
    const rowNumber = index + 1
    if (!Array.isArray(row) || row.length !== GAME_COLUMNS.length) {
      errors.push(`Row ${rowNumber}: expected 6 columns, found ${row?.length ?? 0}.`)
      return
    }

    const values = row.map((value) => String(value ?? '').trim())
    if (values.map((value) => value.toLowerCase()).join('|') === GAME_COLUMNS.join('|')) {
      errors.push(`Row ${rowNumber}: remove the header row; game files are headerless.`)
      return
    }

    const date = normalizedDate(values[0])
    const homeTeam = cleanTeamName(values[1])
    const awayTeam = cleanTeamName(values[2])
    if (!date) errors.push(`Row ${rowNumber}: date must use YYYY-MM-DD or MM/DD/YYYY.`)
    if (!homeTeam) errors.push(`Row ${rowNumber}: home_team is required.`)
    if (!awayTeam) errors.push(`Row ${rowNumber}: away_team is required.`)
    if (homeTeam && awayTeam && homeTeam.toLowerCase() === awayTeam.toLowerCase()) {
      errors.push(`Row ${rowNumber}: home_team and away_team must be different.`)
    }
    if (!/^\d+$/.test(values[3])) {
      errors.push(`Row ${rowNumber}: home_score must be a nonnegative integer.`)
    }
    if (!/^\d+$/.test(values[4])) {
      errors.push(`Row ${rowNumber}: away_score must be a nonnegative integer.`)
    }
    if (!['0', '999'].includes(values[5])) {
      errors.push(`Row ${rowNumber}: neutral_site must be 0 or 999.`)
    }

    if (!date || !homeTeam || !awayTeam) return
    const identity = gameKey(values[0], homeTeam, awayTeam)
    if (identities.has(identity)) {
      errors.push(`Row ${rowNumber}: duplicates row ${identities.get(identity)}.`)
      return
    }
    identities.set(identity, rowNumber)
    games.push([values[0], homeTeam, awayTeam, values[3], values[4], values[5]])
  })

  return { games, errors }
}

export const apiErrorMessages = (error, fallback) => {
  const detail = error.response?.data?.detail
  if (Array.isArray(detail?.errors)) return detail.errors
  if (Array.isArray(detail?.duplicates)) return [detail.message, ...detail.duplicates]
  if (typeof detail === 'string') return [detail]
  if (typeof detail?.message === 'string') return [detail.message]
  return [fallback]
}
