import React from 'react'
import { fireEvent, render, screen, within } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import api from 'src/api'
import Teams from 'src/views/teams/Teams'

jest.mock('src/api', () => ({
  __esModule: true,
  default: {
    get: jest.fn(),
  },
}))

const renderTeams = () =>
  render(
    <MemoryRouter initialEntries={['/basketball/mens/high_school']}>
      <Routes>
        <Route path="/basketball/:gender/:level" element={<Teams fixedSport="basketball" />} />
      </Routes>
    </MemoryRouter>,
  )

beforeEach(() => {
  api.get.mockReset()
})

test('shows a blue message when the selected database has no teams', async () => {
  api.get.mockResolvedValue({
    data: {
      status: 204,
      data: null,
    },
  })

  renderTeams()

  const message = await screen.findByText(
    'No Data Found in Database for High School Mens Basketball',
  )
  expect(
    screen.getByRole('heading', {
      name: 'High School Mens Basketball Ranking',
    }),
  ).toBeInTheDocument()
  expect(message).toHaveClass('text-primary')
})

test('shows a red message when teams data cannot be loaded', async () => {
  const consoleError = jest.spyOn(console, 'error').mockImplementation(() => {})
  api.get.mockRejectedValue(new Error('Network unavailable'))

  renderTeams()

  const message = await screen.findByText('Failed to Load High School Mens Basketball Data')
  expect(
    screen.getByRole('heading', {
      name: 'High School Mens Basketball Ranking',
    }),
  ).toBeInTheDocument()
  expect(message).toHaveClass('text-danger')
  consoleError.mockRestore()
})

test('shows a yearless page title and ranking table headers', async () => {
  api.get.mockResolvedValue({
    data: {
      status: 200,
      data: {
        teams: [{
          id: 1,
          team_name: 'Northstar Academy',
          overall_rank: 1,
          last_rank: 6,
          power_ranking: [{ '2026-01-09': 51.25 }],
          division_rank: 1,
          conference_rank: 3,
          division: '5A',
          conference: 'Western',
          wins: 8,
          losses: 2,
        }, {
          id: 2,
          team_name: 'Central Academy',
          overall_rank: 2,
          last_rank: 12,
          power_ranking: [{ '2026-01-09': 48.75 }],
          division_rank: 1,
          conference_rank: 1,
          division: '4A',
          conference: 'Eastern',
          wins: 6,
          losses: 4,
        }, {
          id: 3,
          team_name: 'Southridge Academy',
          overall_rank: 5,
          last_rank: 3,
          power_ranking: [{ '2026-01-09': 42.5 }],
          division_rank: 2,
          conference_rank: 2,
          division: '3A',
          conference: 'Southern',
          wins: 4,
          losses: 6,
        }],
      },
    },
  })

  renderTeams()

  expect(await screen.findByRole('heading', {
    name: 'High School Mens Basketball Ranking',
  })).toBeInTheDocument()
  expect(await screen.findByRole('columnheader', { name: 'Rank' })).toBeInTheDocument()
  expect(screen.getByRole('table')).toHaveClass('table-striped', 'team-list-table')
  expect(screen.getByRole('columnheader', { name: 'Power' })).toBeInTheDocument()
  expect(screen.getByRole('columnheader', { name: 'Div. Rank' })).toBeInTheDocument()
  expect(screen.getByRole('columnheader', { name: 'LW Rank' })).toBeInTheDocument()
  expect(screen.getByTitle('Last Week Rank')).toHaveTextContent('LW Rank')
  expect(screen.getByRole('columnheader', { name: 'Conference' })).toBeInTheDocument()
  expect(screen.getByRole('columnheader', { name: 'Conf. Rank' })).toBeInTheDocument()
  expect(screen.getByTitle('Conference Rank')).toHaveTextContent('Conf. Rank')
  expect(screen.queryByRole('columnheader', { name: 'Id' })).not.toBeInTheDocument()
  expect(within(screen.getAllByRole('row')[0]).getAllByRole('columnheader').map((header) =>
    header.textContent.trim(),
  )).toEqual([
    'Rank ↑', 'LW Rank', 'Team', 'Power', 'Div. Rank', 'Div.', 'Conference', 'Conf. Rank', 'W', 'L',
  ])
  expect(screen.getByRole('row', { name: /Northstar Academy/ })).toHaveTextContent('3')
  const upFive = screen.getByRole('img', { name: 'Up 5 places' })
  expect(upFive).toHaveTextContent('↑↑')
  expect(upFive).toHaveClass('text-success')
  const upTen = screen.getByRole('img', { name: 'Up 10 places' })
  expect(upTen).toHaveTextContent('↑↑↑')
  expect(upTen).toHaveClass('text-success')
  const downTwo = screen.getByRole('img', { name: 'Down 2 places' })
  expect(downTwo).toHaveTextContent('↓')
  expect(downTwo).toHaveClass('text-danger')
  expect(screen.queryByRole('heading', { name: /\b20\d{2}\b/ })).not.toBeInTheDocument()
  expect(screen.getByRole('combobox', { name: 'Filter by Division' })).toBeInTheDocument()
  expect(screen.getByRole('combobox', { name: 'Filter by Conference' })).toBeInTheDocument()

  fireEvent.change(screen.getByRole('combobox', { name: 'Filter by Division' }), {
    target: { value: '5A' },
  })
  expect(screen.getByRole('link', { name: 'Northstar Academy' })).toBeInTheDocument()
  expect(screen.queryByRole('link', { name: 'Central Academy' })).not.toBeInTheDocument()

  fireEvent.change(screen.getByRole('combobox', { name: 'Filter by Division' }), {
    target: { value: 'all' },
  })
  fireEvent.change(screen.getByRole('combobox', { name: 'Filter by Conference' }), {
    target: { value: 'Eastern' },
  })
  expect(screen.getByRole('link', { name: 'Central Academy' })).toBeInTheDocument()
  expect(screen.queryByRole('link', { name: 'Northstar Academy' })).not.toBeInTheDocument()
})

test('hides conference columns when every team lacks conference data', async () => {
  api.get.mockResolvedValue({
    data: {
      status: 200,
      data: {
        teams: [{
          id: 1,
          team_name: 'Northstar Academy',
          overall_rank: 1,
          last_rank: 1,
          power_ranking: [{ '2026-01-09': 51.25 }],
          division_rank: 1,
          division: '5A',
          conference: ' ',
          conference_rank: 0,
          wins: 8,
          losses: 2,
        }, {
          id: 2,
          team_name: 'Central Academy',
          overall_rank: 2,
          last_rank: 2,
          power_ranking: [{ '2026-01-09': 48.75 }],
          division_rank: 1,
          division: '4A',
          conference: null,
          conference_rank: null,
          wins: 6,
          losses: 4,
        }],
      },
    },
  })

  renderTeams()

  expect(await screen.findByRole('columnheader', { name: 'Rank' })).toBeInTheDocument()
  expect(screen.queryByRole('columnheader', { name: 'Conference' })).not.toBeInTheDocument()
  expect(screen.queryByRole('columnheader', { name: 'Conf. Rank' })).not.toBeInTheDocument()
})

test('displays and sorts unranked teams at rank 9999', async () => {
  api.get.mockResolvedValue({
    data: {
      status: 200,
      data: {
        teams: [{
          id: 1,
          team_name: 'Unranked Academy',
          overall_rank: 0,
          last_rank: 0,
          power_ranking: [],
          division_rank: 0,
          division: '5A',
          wins: 0,
          losses: 0,
        }, {
          id: 2,
          team_name: 'Ranked Academy',
          overall_rank: 4,
          last_rank: 4,
          power_ranking: [],
          division_rank: 1,
          division: '5A',
          wins: 5,
          losses: 2,
        }],
      },
    },
  })

  renderTeams()

  await screen.findByRole('link', { name: 'Unranked Academy' })
  expect(screen.getByRole('row', { name: /Unranked Academy/ })).toHaveTextContent('9999')
  const rankHeader = screen.getByRole('columnheader', { name: 'Rank' })
  expect(rankHeader).toHaveAttribute('aria-sort', 'ascending')
  expect(screen.getAllByRole('link').map((link) => link.textContent)).toEqual([
    'Ranked Academy',
    'Unranked Academy',
  ])
  fireEvent.click(rankHeader)
  expect(rankHeader).toHaveAttribute('aria-sort', 'descending')
  expect(screen.getAllByRole('link').map((link) => link.textContent)).toEqual([
    'Unranked Academy',
    'Ranked Academy',
  ])
})

test('sorts by last week rank with unranked teams last', async () => {
  const team = (id, teamName, overallRank, lastRank) => ({
    id,
    team_name: teamName,
    overall_rank: overallRank,
    last_rank: lastRank,
    power_ranking: [],
    division_rank: 1,
    division: '5A',
    wins: 0,
    losses: 0,
  })
  api.get.mockResolvedValue({
    data: {
      status: 200,
      data: {
        teams: [
          team(1, 'Alpha Academy', 1, 3),
          team(2, 'Bravo Academy', 2, 0),
          team(3, 'Charlie Academy', 3, 1),
        ],
      },
    },
  })

  renderTeams()

  await screen.findByRole('link', { name: 'Alpha Academy' })
  const lwRankHeader = screen.getByRole('columnheader', { name: 'LW Rank' })
  const teamOrder = () => screen.getAllByRole('link').map((link) => link.textContent)

  fireEvent.click(lwRankHeader)
  expect(lwRankHeader).toHaveAttribute('aria-sort', 'ascending')
  expect(screen.getByRole('columnheader', { name: 'Rank' })).not.toHaveAttribute('aria-sort')
  expect(teamOrder()).toEqual(['Charlie Academy', 'Alpha Academy', 'Bravo Academy'])

  fireEvent.click(lwRankHeader)
  expect(lwRankHeader).toHaveAttribute('aria-sort', 'descending')
  expect(teamOrder()).toEqual(['Bravo Academy', 'Alpha Academy', 'Charlie Academy'])
})

test('shows conference rank for conference sports before rankings are calculated', async () => {
  const team = (id, teamName, conference, conferenceRank) => ({
    id,
    team_name: teamName,
    overall_rank: id,
    last_rank: 0,
    power_ranking: [],
    division_rank: 1,
    division: '5A',
    conference,
    conference_rank: conferenceRank,
    wins: 0,
    losses: 0,
  })
  api.get.mockResolvedValue({
    data: {
      status: 200,
      data: {
        teams: [
          team(1, 'Alpha Academy', 'Northern', 0),
          team(2, 'Bravo Academy', 'Northern', 2),
          team(3, 'Charlie Academy', 'Southern', 1),
        ],
      },
    },
  })

  renderTeams()

  await screen.findByRole('link', { name: 'Alpha Academy' })
  const confRankHeader = screen.getByRole('columnheader', { name: 'Conf. Rank' })
  const alphaCells = within(screen.getByRole('row', { name: /Alpha Academy/ })).getAllByRole('cell')
  expect(alphaCells[7]).toHaveTextContent('-')

  fireEvent.click(confRankHeader)
  expect(confRankHeader).toHaveAttribute('aria-sort', 'ascending')
  expect(screen.getAllByRole('link').map((link) => link.textContent)).toEqual([
    'Charlie Academy', 'Bravo Academy', 'Alpha Academy',
  ])
})
