import React from 'react'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
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
    if (
      params.sport_type === 'basketball' &&
      params.gender === 'mens' &&
      params.level === 'high_school'
    ) {
      return Promise.resolve({
        status: 200,
        data: {
          status: 200,
          data: {
            teams: [{ id: 1, team_name: 'Northstar Academy', overall_rank: 3 }],
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
  expect(screen.getByText('Basketball')).toBeInTheDocument()
  expect(screen.getByText('High School')).toBeInTheDocument()
})
