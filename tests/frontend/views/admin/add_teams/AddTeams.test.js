import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import api from 'src/api'
import AddTeams from 'src/views/admin/add_teams/AddTeams'

jest.mock('src/api', () => ({
  __esModule: true,
  default: { get: jest.fn(), post: jest.fn() },
}))

jest.mock('react-redux', () => ({
  useSelector: (selector) => selector({
    sport: 'basketball',
    gender: 'womens',
    level: 'college',
  }),
}))

beforeEach(() => {
  api.get.mockReset()
  api.post.mockReset()
})

test('uploads a team metadata CSV and reports only the teams that failed with a reason', async () => {
  const user = userEvent.setup()
  api.post.mockResolvedValue({
    data: {
      message: 'Added 1 team; failed to add 1 team.',
      teams_added_count: 1,
      teams_failed: [{
        team_name: 'AK Anchorage',
        reason: 'A team with this short or long name already exists in the database',
      }],
    },
  })
  render(<AddTeams />)

  const file = new File([
    'state,short_name,team_id,long_name,division,conference,ranked\n'
    + 'Alaska,North Alaska,1003,University of North Alaska,NCAA 2,GNAC,yes\n',
  ], 'teams.csv', { type: 'text/csv' })
  await user.upload(screen.getByLabelText('Choose Team Data CSV'), file)
  await user.click(screen.getByRole('button', { name: 'Upload Team Data' }))

  await waitFor(() => expect(api.post).toHaveBeenCalledWith(
    '/teams/upload/?sport_type=basketball&gender=womens&level=college',
    expect.any(FormData),
  ))
  expect(await screen.findByText(
    'AK Anchorage: A team with this short or long name already exists in the database',
  )).toBeInTheDocument()
  expect(screen.queryByText(/North Alaska/)).not.toBeInTheDocument()
})

test('shows server header errors when the team file format is incorrect', async () => {
  const user = userEvent.setup()
  api.post.mockRejectedValue({
    response: {
      data: {
        detail: {
          message: 'Team data file format is not correct',
          errors: ['File format is not correct. Missing required headers: ranked.'],
        },
      },
    },
  })
  render(<AddTeams />)

  const file = new File(['state,short_name\nAlaska,Anchorage'], 'bad.csv', {
    type: 'text/csv',
  })
  await user.upload(screen.getByLabelText('Choose Team Data CSV'), file)
  await user.click(screen.getByRole('button', { name: 'Upload Team Data' }))

  expect(await screen.findByText(/Missing required headers: ranked/)).toBeInTheDocument()
})

test('adds one team with all CSV fields through the manual form', async () => {
  const user = userEvent.setup()
  api.get.mockResolvedValue({
    status: 200,
    data: {
      status: 200,
      data: { teams: [{ team_id: 713 }, { team_id: 1002 }] },
    },
  })
  api.post.mockResolvedValue({ data: { added: ['North Alaska'], skipped: [] } })
  render(<AddTeams />)

  await user.click(screen.getByRole('button', { name: 'Add One Team' }))
  expect(screen.getByLabelText('Included in Ranking?')).toHaveValue('yes')
  await waitFor(() => expect(screen.getByLabelText('Team ID')).toHaveValue(1003))
  expect(api.get).toHaveBeenCalledWith('/teams-ids/', {
    params: { sport_type: 'basketball', gender: 'womens', level: 'college' },
  })
  expect(screen.getByRole('option', { name: 'British Columbia' })).toBeInTheDocument()
  await user.selectOptions(screen.getByLabelText('State'), 'British Columbia')
  await user.type(screen.getByLabelText('Short Name'), 'North Alaska')
  await user.type(screen.getByLabelText('Long Name'), 'University of North Alaska')
  await user.type(screen.getByLabelText('Division'), 'NCAA 2')
  await user.type(screen.getByLabelText('Conference'), 'GNAC')
  await user.click(screen.getByRole('button', { name: 'Add Team' }))

  await waitFor(() => expect(api.post).toHaveBeenCalledWith(
    '/add_teams/?sport_type=basketball&gender=womens&level=college',
    [{
      team_id: 1003,
      state: 'British Columbia',
      short_name: 'North Alaska',
      long_name: 'University of North Alaska',
      division: 'NCAA 2',
      conference: 'GNAC',
      ranked: true,
    }],
  ))
  expect(await screen.findByText('Team added successfully')).toBeInTheDocument()
  expect(screen.getByLabelText('State')).toHaveValue('')
  expect(screen.getByLabelText('Team ID')).toHaveValue(1004)
})

test('shows the duplicate reason when the manually added team already exists', async () => {
  const user = userEvent.setup()
  api.get.mockResolvedValue({ status: 204, data: null })
  api.post.mockResolvedValue({
    data: {
      added: [],
      skipped: [{
        team_name: 'AK Anchorage',
        reason: 'A team with this short or long name already exists in the database',
      }],
    },
  })
  render(<AddTeams />)

  await user.click(screen.getByRole('button', { name: 'Add One Team' }))
  await waitFor(() => expect(screen.getByLabelText('Team ID')).toHaveValue(1))
  await user.selectOptions(screen.getByLabelText('State'), 'Alaska')
  await user.type(screen.getByLabelText('Short Name'), 'AK Anchorage')
  await user.click(screen.getByRole('button', { name: 'Add Team' }))

  expect(await screen.findByText(
    'AK Anchorage: A team with this short or long name already exists in the database',
  )).toBeInTheDocument()
})
