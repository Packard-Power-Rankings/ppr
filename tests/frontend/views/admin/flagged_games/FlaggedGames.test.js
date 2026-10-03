import React from 'react'
import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import api from 'src/api'
import FlaggedGames from 'src/views/admin/flagged_games/FlaggedGames'

jest.mock('src/api', () => ({
  __esModule: true,
  default: {
    get: jest.fn(),
    patch: jest.fn(),
  },
}))

const longDescription = 'The score and home team are incorrect. '.repeat(5)

beforeEach(() => {
  api.get.mockReset()
  api.patch.mockReset()
})

test('lists oldest issues first, expands details, and resolves one issue', async () => {
  const user = userEvent.setup()
  api.get
    .mockResolvedValueOnce({
      data: {
        count: 2,
        issues: [
          {
            issue_id: 'older-issue',
            game_id: 'game-1',
            team1_id: 1,
            team1_name: 'Northstar',
            team2_id: 2,
            team2_name: 'Ridgeview',
            description: longDescription,
            reported_at: '2026-09-01T12:00:00Z',
            sport_type: 'basketball',
            gender: 'mens',
            level: 'high_school',
          },
          {
            issue_id: 'newer-issue',
            game_id: 'game-2',
            team1_name: 'Central',
            team2_name: 'West',
            description: 'The final score is incorrect.',
            reported_at: '2026-09-02T12:00:00Z',
            sport_type: 'football',
            gender: 'mens',
            level: 'college',
          },
        ],
      },
    })
  api.patch.mockResolvedValue({ data: { message: 'Flagged game issue resolved' } })

  render(
    <MemoryRouter>
      <FlaggedGames />
    </MemoryRouter>,
  )

  expect(await screen.findByText('2 unresolved issues')).toBeInTheDocument()
  const rows = screen.getAllByRole('row').slice(1)
  expect(within(rows[0]).getByText('Northstar vs Ridgeview')).toBeInTheDocument()
  expect(within(rows[1]).getByText('Central vs West')).toBeInTheDocument()
  expect(screen.getByText('High School Mens Basketball')).toBeInTheDocument()
  expect(within(rows[0]).getByRole('link', {
    name: 'Update game Northstar vs Ridgeview',
  })).toHaveAttribute('href', '/admin/update_game')

  await user.click(within(rows[0]).getByRole('button', { name: /view details/i }))
  const detailDialog = await screen.findByRole('dialog')
  expect(within(detailDialog).getByText(/The score and home team are incorrect/))
    .toHaveTextContent(longDescription.trim())
  await user.click(within(detailDialog).getByText('Close'))

  await user.click(screen.getByRole('button', {
    name: 'Resolve issue for Northstar vs Ridgeview',
  }))
  const resolveDialog = await screen.findByRole('dialog')
  await user.click(within(resolveDialog).getByRole('button', { name: 'Resolve Issue' }))

  await waitFor(() => expect(api.patch).toHaveBeenCalledWith(
    '/flagged-games/older-issue/resolve',
  ))
  expect(await screen.findByText('The game issue was marked as resolved.')).toBeInTheDocument()
  expect(screen.getByText('1 unresolved issue')).toBeInTheDocument()
  expect(screen.queryByText('Northstar vs Ridgeview')).not.toBeInTheDocument()
  expect(screen.getByText('Central vs West')).toBeInTheDocument()
  expect(api.get).toHaveBeenCalledTimes(1)
})
