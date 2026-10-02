import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Provider } from 'react-redux'
import { legacy_createStore as createStore } from 'redux'
import api from 'src/api'
import Papa from 'papaparse'
import AddGames from 'src/views/admin/add_games/AddGames'

jest.mock('src/api', () => ({
  __esModule: true,
  default: { get: jest.fn(), post: jest.fn() },
}))

jest.mock('papaparse', () => ({
  __esModule: true,
  default: {
    parse: jest.fn(),
    unparse: jest.fn(() => '2026-01-15,Central High,Lincoln High,72,68,0'),
  },
}))

const state = {
  sport: 'basketball',
  gender: 'mens',
  level: 'high_school',
}

const renderPage = () => render(
  <Provider store={createStore((currentState = state) => currentState)}>
    <AddGames />
  </Provider>,
)

beforeEach(() => {
  api.get.mockReset()
  api.get.mockResolvedValue({
    status: 200,
    data: {
      status: 200,
      data: {
        teams: [
          { team_id: 1, team_name: 'Central High' },
          { team_id: 2, team_name: 'Lincoln High' },
        ],
      },
    },
  })
  api.post.mockReset()
  Papa.parse.mockReset()
  Papa.unparse.mockClear()
})

test('confirms the selected dataset before parsing and uploads a valid file', async () => {
  const user = userEvent.setup()
  Papa.parse.mockImplementation((_file, options) => options.complete({
    data: [['2026-01-15', 'Central High', 'Lincoln High', '72', '68', '0']],
    errors: [],
  }))
  api.post.mockResolvedValue({
    data: {
      message: 'Added 1 game to mens high_school basketball',
    },
  })
  renderPage()

  expect(screen.getByRole('heading', {
    name: 'Upload Game File For Mens High School Basketball',
  })).toBeInTheDocument()

  const file = new File(
    ['2026-01-15,Central High,Lincoln High,72,68,0'],
    'week-01.csv',
    { type: 'text/csv' },
  )
  await user.upload(screen.getByLabelText('Choose CSV game file'), file)

  expect(await screen.findByRole('heading', { name: 'Confirm Game File' })).toBeInTheDocument()
  expect(Papa.parse).not.toHaveBeenCalled()

  await user.click(screen.getByRole('button', { name: 'Yes, Parse File' }))
  expect(Papa.parse).toHaveBeenCalledWith(file, expect.objectContaining({
    complete: expect.any(Function),
  }))
  expect(await screen.findByText('Central High')).toBeInTheDocument()

  await user.click(screen.getByRole('button', { name: 'Submit Game File' }))
  await waitFor(() => expect(api.post).toHaveBeenCalledWith(
    '/games/upload/?sport_type=basketball&gender=mens&level=high_school',
    expect.any(FormData),
  ))
  expect(await screen.findByText('Added 1 game to mens high_school basketball'))
    .toBeInTheDocument()
})

test('shows the required CSV columns and example from the help icon', async () => {
  const user = userEvent.setup()
  renderPage()

  await user.click(screen.getByRole('button', { name: 'Show game file format' }))

  expect(await screen.findByRole('heading', { name: 'CSV Game File Format' })).toBeInTheDocument()
  expect(screen.getByText('home_team')).toBeInTheDocument()
  expect(screen.getByText('2026-01-15')).toBeInTheDocument()
  expect(screen.getByText('999')).toBeInTheDocument()
})

test('adds one game through the same selected dataset workflow', async () => {
  const user = userEvent.setup()
  api.post.mockResolvedValue({ data: { message: 'Added 1 game' } })
  renderPage()

  await user.click(screen.getByRole('button', { name: 'Add One Game' }))
  await user.type(screen.getByLabelText('Game Date'), '2026-01-15')
  await user.click(screen.getByLabelText('Home Team'))
  await user.type(screen.getByLabelText('Home Team'), 'Central')
  await user.click(await screen.findByRole('option', { name: 'Central High' }))
  await user.click(screen.getByLabelText('Away Team'))
  await user.type(screen.getByLabelText('Away Team'), 'Lincoln')
  await user.click(await screen.findByRole('option', { name: 'Lincoln High' }))
  await user.type(screen.getByLabelText('Home Score'), '72')
  await user.type(screen.getByLabelText('Away Score'), '68')
  await user.selectOptions(screen.getByLabelText('Location'), '999')
  await user.click(screen.getByRole('button', { name: 'Add Game' }))

  await waitFor(() => expect(api.post).toHaveBeenCalledWith(
    '/games/?sport_type=basketball&gender=mens&level=high_school',
    {
      date: '2026-01-15',
      home_team: 'Central High',
      away_team: 'Lincoln High',
      home_score: 72,
      away_score: 68,
      neutral_site: 999,
    },
  ))
})

test('shows unknown teams returned by the game endpoint', async () => {
  const user = userEvent.setup()
  api.post.mockRejectedValue({
    response: {
      data: {
        detail: {
          message: 'Import team data before adding games.',
          unknown_teams: ['Lincoln High'],
          errors: ['Unknown team: Lincoln High'],
        },
      },
    },
  })
  renderPage()

  await user.click(screen.getByRole('button', { name: 'Add One Game' }))
  await user.type(screen.getByLabelText('Game Date'), '2026-01-15')
  await user.click(screen.getByLabelText('Home Team'))
  await user.click(await screen.findByRole('option', { name: 'Central High' }))
  await user.click(screen.getByLabelText('Away Team'))
  await user.click(await screen.findByRole('option', { name: 'Lincoln High' }))
  await user.type(screen.getByLabelText('Home Score'), '72')
  await user.type(screen.getByLabelText('Away Score'), '68')
  await user.click(screen.getByRole('button', { name: 'Add Game' }))

  expect(await screen.findByText('Unknown team: Lincoln High')).toBeInTheDocument()
})
