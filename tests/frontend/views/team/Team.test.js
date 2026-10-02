import React from 'react'
import { render, screen, within } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import api from 'src/api'
import Team from 'src/views/team/Team'

jest.mock('src/api', () => ({
  __esModule: true,
  default: {
    get: jest.fn(),
    post: jest.fn(),
  },
}))

beforeEach(() => {
  api.get.mockReset()
  api.post.mockReset()
})

test('labels team rankings without the ranking year', async () => {
  api.get.mockResolvedValue({
    data: {
      data: {
        teams: {
          team_id: 1,
          team_name: 'Northstar Academy',
          overall_rank: 2,
          division_rank: 1,
          conference_rank: 3,
          last_rank: 4,
          division: '5A',
          conference: 'Western',
          state: 'North Dakota',
          power_ranking: [{ '2026-02-01': 51.25 }],
          wins: 0,
          losses: 0,
          season_opp: [],
        },
      },
    },
  })

  render(
    <MemoryRouter initialEntries={[
      '/team/Northstar%20Academy/basketball/mens/high_school',
    ]}>
      <Routes>
        <Route path="/team/:team_name/:sport/:gender/:level" element={<Team />} />
      </Routes>
    </MemoryRouter>,
  )

  const teamTitle = await screen.findByRole('heading', { name: 'Northstar Academy' })
  const overallRank = screen.getByRole('heading', { name: 'Rank: 2' })
  const powerRank = screen.getByRole('heading', { name: 'Power: 51.25' })
  const divisionRank = screen.getByRole('heading', { name: 'Division Rank: 1' })
  const conferenceRank = screen.getByRole('heading', { name: 'Conference Rank: 3' })
  expect(screen.getByRole('heading', { name: 'Last Rank: 4' })).toBeInTheDocument()
  expect(screen.getByRole('heading', { name: 'State: North Dakota' })).toBeInTheDocument()
  expect(teamTitle.parentElement).not.toBe(overallRank.parentElement)
  expect(overallRank.closest('.row')).toBe(powerRank.closest('.row'))
  expect(divisionRank.closest('.row')).toBe(conferenceRank.closest('.row'))
  expect(overallRank.closest('.row')).not.toBe(divisionRank.closest('.row'))
})

test('highlights wins and losses from the displayed team perspective', async () => {
  api.get.mockResolvedValue({
    data: {
      data: {
        teams: {
          team_id: 1,
          overall_rank: 2,
          division_rank: 1,
          power_ranking: [{ '2026-02-01': 51.25 }],
          season_opp: [
            {
              opponent_name: 'Home win opponent',
              game_date: '2026-01-10',
              home_team: 1,
              home_score: 24,
              away_score: 10,
              home_z_score: 1,
              away_z_score: -1,
            },
            {
              opponent_name: 'Home loss opponent',
              game_date: '2026-01-08',
              home_team: 1,
              home_score: 7,
              away_score: 21,
              home_z_score: -1,
              away_z_score: 1,
            },
            {
              opponent_name: 'Away win opponent',
              game_date: '2026-01-09',
              home_team: 0,
              home_score: 10,
              away_score: 17,
              home_z_score: -1,
              away_z_score: 1,
            },
            {
              opponent_name: 'Away loss opponent',
              game_date: '2026-01-07',
              home_team: 0,
              home_score: 31,
              away_score: 14,
              home_z_score: 1,
              away_z_score: -1,
            },
            {
              opponent_name: 'Draw opponent',
              game_date: '2026-01-11',
              home_team: 0,
              home_score: 14,
              away_score: 14,
              home_z_score: 0,
              away_z_score: 0,
            },
          ],
        },
      },
    },
  })

  render(
    <MemoryRouter initialEntries={['/team/Northstar%20Academy/basketball/mens/high_school']}>
      <Routes>
        <Route path="/team/:team_name/:sport/:gender/:level" element={<Team />} />
      </Routes>
    </MemoryRouter>,
  )

  const homeWin = await screen.findByText('Home win opponent')
  const homeLoss = screen.getByText('Home loss opponent')
  const awayWin = screen.getByText('Away win opponent')
  const awayLoss = screen.getByText('Away loss opponent')
  const draw = screen.getByText('Draw opponent')

  const opponentRows = screen.getAllByRole('row').slice(1)
  expect(opponentRows.map((row) => within(row).getByRole('link').textContent)).toEqual([
    'Draw opponent',
    'Home win opponent',
    'Away win opponent',
    'Home loss opponent',
    'Away loss opponent',
  ])

  expect(homeWin.closest('a')).toHaveAttribute(
    'href',
    '/team/Home%20win%20opponent/basketball/mens/high_school',
  )

  expect(homeWin.closest('tr')).toHaveClass('table-success')
  expect(homeLoss.closest('tr')).toHaveClass('table-danger')
  expect(awayWin.closest('tr')).toHaveClass('table-success')
  expect(awayLoss.closest('tr')).toHaveClass('table-danger')
  expect(draw.closest('tr')).not.toHaveClass('table-success', 'table-danger')
  expect(within(draw.closest('tr')).getByText('Draw')).toBeInTheDocument()
})

test('shows short name and long name in the card title when both are present', async () => {
  api.get.mockResolvedValue({
    data: {
      data: {
        teams: {
          team_id: 1,
          team_name: 'CMU',
          short_name: 'CMU',
          long_name: 'Central Michigan University',
          overall_rank: 1,
          division_rank: 1,
          power_ranking: [],
          wins: 0,
          losses: 0,
          season_opp: [],
        },
      },
    },
  })

  render(
    <MemoryRouter initialEntries={['/team/CMU/basketball/mens/college']}>
      <Routes>
        <Route path="/team/:team_name/:sport/:gender/:level" element={<Team />} />
      </Routes>
    </MemoryRouter>,
  )

  expect(await screen.findByRole('heading', {
    name: 'CMU - Central Michigan University',
    level: 3,
  })).toBeInTheDocument()
})

test('falls back to the team name when short and long names are unavailable', async () => {
  api.get.mockResolvedValue({
    data: {
      data: {
        teams: {
          team_id: 1,
          overall_rank: 1,
          division_rank: 1,
          power_ranking: [],
          wins: 0,
          losses: 0,
          season_opp: [],
        },
      },
    },
  })

  render(
    <MemoryRouter initialEntries={['/team/Northstar%20Academy/basketball/mens/high_school']}>
      <Routes>
        <Route path="/team/:team_name/:sport/:gender/:level" element={<Team />} />
      </Routes>
    </MemoryRouter>,
  )

  expect(await screen.findByRole('heading', {
    name: 'Northstar Academy',
    level: 3,
  })).toBeInTheDocument()
})
