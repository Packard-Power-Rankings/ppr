import React from 'react'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import api from 'src/api'
import Archive from 'src/views/archive/Archive'

jest.mock('src/api', () => ({
  __esModule: true,
  default: {
    get: jest.fn(),
  },
}))

const archivedSeason = {
  year: 2026,
  dataset_count: 2,
  team_count: 3,
  datasets: [
    {
      sport: 'football',
      gender: 'mens',
      level: 'college',
      label: 'College Mens Football',
      slug: 'football-mens-college',
      team_count: 1,
      static_url: '/archive/2026/football-mens-college.html',
      teams: [
        {
          id: 3,
          rank: 1,
          team_name: 'Summit University',
          power: 62.5,
          division_rank: 1,
          division: 'NCAA 1',
          wins: 11,
          losses: 1,
        },
      ],
    },
    {
      sport: 'basketball',
      gender: 'mens',
      level: 'high_school',
      label: 'High School Mens Basketball',
      slug: 'basketball-mens-high-school',
      team_count: 2,
      static_url: '/archive/2026/basketball-mens-high-school.html',
      teams: [
        {
          id: 1,
          rank: 1,
          team_name: 'Northstar Academy',
          power: 51.25,
          division_rank: 1,
          division: '5A',
          wins: 10,
          losses: 0,
        },
        {
          id: 2,
          rank: 2,
          team_name: 'Cedar Valley',
          power: 48.1,
          division_rank: 2,
          division: '5A',
          wins: 8,
          losses: 2,
        },
      ],
    },
  ],
}

beforeEach(() => {
  api.get.mockReset()
})

test('lists available seasons and their ranking datasets', async () => {
  api.get.mockResolvedValue({
    data: {
      archives: [{
        year: 2026,
        dataset_count: 2,
        team_count: 3,
        datasets: archivedSeason.datasets,
      }],
    },
  })

  render(
    <MemoryRouter initialEntries={['/archives']}>
      <Routes>
        <Route path="/archives" element={<Archive />} />
      </Routes>
    </MemoryRouter>,
  )

  expect(await screen.findByRole('heading', { name: 'Season Archives' })).toBeInTheDocument()
  expect(screen.getByRole('link', { name: /High School Mens Basketball/ })).toHaveAttribute(
    'href',
    '/archives/2026/basketball-mens-high-school',
  )
})

test('displays and searches a selected archived ranking', async () => {
  const user = userEvent.setup()
  api.get.mockResolvedValue({ data: archivedSeason })

  render(
    <MemoryRouter initialEntries={['/archives/2026/basketball-mens-high-school']}>
      <Routes>
        <Route path="/archives/:year/:dataset" element={<Archive />} />
      </Routes>
    </MemoryRouter>,
  )

  expect(
    await screen.findByRole('heading', { name: '2026 Season Archive' }),
  ).toBeInTheDocument()
  expect(screen.getByRole('cell', { name: 'Northstar Academy' })).toBeInTheDocument()
  expect(screen.getByRole('cell', { name: 'Cedar Valley' })).toBeInTheDocument()
  expect(screen.getByRole('link', { name: 'Open this static page' })).toHaveAttribute(
    'href',
    '/archive/2026/basketball-mens-high-school.html',
  )

  await user.type(screen.getByRole('searchbox', { name: 'Search archived teams' }), 'Cedar')

  expect(screen.queryByRole('cell', { name: 'Northstar Academy' })).not.toBeInTheDocument()
  expect(screen.getByRole('cell', { name: 'Cedar Valley' })).toBeInTheDocument()
})
