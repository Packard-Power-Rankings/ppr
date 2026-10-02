import React from 'react'
import { fireEvent, render, screen, within } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import api from 'src/api'
import AllTeams from 'src/views/teams/AllTeams'

jest.mock('src/api', () => ({
  __esModule: true,
  default: {
    get: jest.fn(),
  },
}))

beforeEach(() => {
  api.get.mockReset()
})

test('lists teams from every dataset and links to their detail pages', async () => {
  api.get.mockImplementation((_url, { params }) => {
    const datasetTeams = {
      'basketball-mens-high_school': [{
        id: 1,
        team_name: 'Northstar Academy',
        overall_rank: 3,
        power_ranking: [{ '2026-10-01': 42.125 }],
        division_rank: 1,
        last_rank: 5,
      }],
      'basketball-womens-high_school': [{ id: 2, team_name: 'Southern Stars' }],
      'basketball-mens-college': [{ id: 3, team_name: 'Northstar College' }],
      'football-mens-high_school': [{ id: 4, team_name: 'Falcons' }],
    }
    const key = `${params.sport_type}-${params.gender}-${params.level}`
    if (datasetTeams[key]) {
      return Promise.resolve({
        status: 200,
        data: {
          status: 200,
          data: {
            teams: datasetTeams[key],
          },
        },
      })
    }

    return Promise.resolve({ status: 200, data: { status: 204, data: null } })
  })

  render(
    <MemoryRouter>
      <AllTeams />
    </MemoryRouter>,
  )

  const teamLink = await screen.findByRole('link', { name: 'Northstar Academy' })
  expect(teamLink).toHaveAttribute(
    'href',
    '/team/Northstar%20Academy/basketball/mens/high_school',
  )
  expect(api.get).toHaveBeenCalledTimes(6)
  expect(within(teamLink.closest('tr')).getByText('Basketball')).toBeInTheDocument()
  expect(within(teamLink.closest('tr')).getByText('Mens')).toBeInTheDocument()
  expect(within(teamLink.closest('tr')).getByText('High School')).toBeInTheDocument()
  expect(screen.getByRole('columnheader', { name: 'Rank' })).toBeInTheDocument()
  expect(screen.getByRole('columnheader', { name: 'Power' })).toBeInTheDocument()
  expect(screen.getByRole('columnheader', { name: 'Div Rank' })).toBeInTheDocument()
  expect(screen.getByRole('columnheader', { name: 'Last Rank' })).toBeInTheDocument()
  expect(screen.getByText('42.13')).toBeInTheDocument()
  expect(screen.getByText('1')).toBeInTheDocument()
  expect(screen.getByText('5')).toBeInTheDocument()
  expect(screen.getByRole('table')).toHaveClass('table-striped', 'team-list-table')

  fireEvent.change(screen.getByRole('combobox', { name: 'Filter by Sport' }), {
    target: { value: 'basketball' },
  })
  expect(screen.queryByRole('link', { name: 'Falcons' })).not.toBeInTheDocument()
  expect(screen.getByRole('link', { name: 'Southern Stars' })).toBeInTheDocument()

  fireEvent.change(screen.getByRole('combobox', { name: 'Filter by Sport' }), {
    target: { value: 'all' },
  })
  fireEvent.change(screen.getByRole('combobox', { name: 'Filter by Gender' }), {
    target: { value: 'womens' },
  })
  expect(screen.getByRole('link', { name: 'Southern Stars' })).toBeInTheDocument()
  expect(screen.queryByRole('link', { name: 'Northstar Academy' })).not.toBeInTheDocument()

  fireEvent.change(screen.getByRole('combobox', { name: 'Filter by Gender' }), {
    target: { value: 'all' },
  })
  fireEvent.change(screen.getByRole('combobox', { name: 'Filter by Level' }), {
    target: { value: 'college' },
  })
  expect(screen.getByRole('link', { name: 'Northstar College' })).toBeInTheDocument()
  expect(screen.queryByRole('link', { name: 'Falcons' })).not.toBeInTheDocument()
})

test('hides sport and gender columns when the route already specifies both', async () => {
  api.get.mockResolvedValue({
    status: 200,
    data: {
      status: 200,
      data: {
        teams: [{ id: 1, team_name: 'Northstar Academy', overall_rank: 3 }],
      },
    },
  })

  render(
    <MemoryRouter initialEntries={['/football/mens']}>
      <Routes>
        <Route path="/football/:gender" element={<AllTeams fixedSport="football" />} />
      </Routes>
    </MemoryRouter>,
  )

  await screen.findByRole('columnheader', { name: 'Level' })
  expect(screen.getByRole('combobox', { name: 'Filter by Level' })).toBeInTheDocument()
  expect(screen.queryByRole('combobox', { name: 'Filter by Sport' })).not.toBeInTheDocument()
  expect(screen.queryByRole('combobox', { name: 'Filter by Gender' })).not.toBeInTheDocument()
  expect(screen.queryByRole('columnheader', { name: 'Sport' })).not.toBeInTheDocument()
  expect(screen.queryByRole('columnheader', { name: 'Gender' })).not.toBeInTheDocument()
})
