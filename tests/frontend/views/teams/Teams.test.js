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
  expect(screen.getByRole('columnheader', { name: 'Last Rank' })).toBeInTheDocument()
  expect(screen.getByRole('columnheader', { name: 'Conference' })).toBeInTheDocument()
  expect(screen.getByRole('columnheader', { name: 'Cnf. Rank' })).toBeInTheDocument()
  expect(screen.queryByRole('columnheader', { name: 'Id' })).not.toBeInTheDocument()
  expect(within(screen.getAllByRole('row')[0]).getAllByRole('columnheader').map((header) =>
    header.textContent.trim(),
  )).toEqual([
    'Rank', 'Last Rank', 'Team', 'Power', 'Div. Rank', 'Div.', 'Conference', 'Cnf. Rank', 'W', 'L',
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
  expect(screen.queryByRole('columnheader', { name: 'Cnf. Rank' })).not.toBeInTheDocument()
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
  fireEvent.click(screen.getByRole('columnheader', { name: 'Rank' }))
  expect(screen.getAllByRole('link').map((link) => link.textContent)).toEqual([
    'Ranked Academy',
    'Unranked Academy',
  ])
})
