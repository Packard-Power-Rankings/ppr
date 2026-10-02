import React from 'react'
import { render, screen } from '@testing-library/react'
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
          power_ranking: [{ '2026-01-09': 51.25 }],
          division_rank: 1,
          division: '5A',
          wins: 8,
          losses: 2,
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
  expect(screen.queryByRole('heading', { name: /\b20\d{2}\b/ })).not.toBeInTheDocument()
})
