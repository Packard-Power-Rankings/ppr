import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Provider } from 'react-redux'
import { legacy_createStore as createStore } from 'redux'
import { MemoryRouter } from 'react-router-dom'
import api from 'src/api'
import UpdateGame from 'src/views/admin/update_game/UpdateGame'

jest.mock('src/api', () => ({
  __esModule: true,
  default: {
    get: jest.fn(),
    put: jest.fn(),
  },
}))

const reducer = (
  state = { sport: 'basketball', gender: 'mens', level: 'high_school' },
  action,
) => (action.type === 'updateAdminState' ? { ...state, ...action.payload } : state)

beforeEach(() => {
  api.get.mockReset()
  api.put.mockReset()
})

test('loads a game and submits its corrected scores', async () => {
  const user = userEvent.setup()
  const store = createStore(reducer)

  api.get.mockImplementation((url) => {
    if (url === '/teams-ids/') {
      return Promise.resolve({
        status: 200,
        data: {
          status: 200,
          data: {
            teams: [
              { team_id: 1, team_name: 'Northstar Academy' },
              { team_id: 2, team_name: 'Cedar Valley' },
            ],
          },
        },
      })
    }

    return Promise.resolve({
      data: [
        {
          game_id: '1_2_2026-01-09',
          game_date: '2026-01-09',
          home_team_id: 1,
          home_team_name: 'Northstar Academy',
          away_team_id: 2,
          away_team_name: 'Cedar Valley',
          home_score: 72,
          away_score: 61,
        },
      ],
    })
  })
  api.put.mockResolvedValue({
    data: {
      status: 200,
      message: 'Updated Northstar Academy vs Cedar Valley on 2026-01-09',
    },
  })

  render(
    <Provider store={store}>
      <MemoryRouter>
        <UpdateGame />
      </MemoryRouter>
    </Provider>,
  )

  await user.click(await screen.findByRole('combobox', { name: 'First Team' }))
  await user.click(await screen.findByText('Northstar Academy'))
  await user.click(screen.getByRole('combobox', { name: 'Second Team' }))
  await user.click(await screen.findByText('Cedar Valley'))
  await user.click(screen.getByRole('button', { name: 'Find Games' }))

  await user.click(await screen.findByRole('combobox', { name: 'Game' }))
  await user.click(
    await screen.findByText('2026-01-09: Northstar Academy 72 - 61 Cedar Valley'),
  )

  const homeScore = screen.getByLabelText('Northstar Academy Score')
  await user.clear(homeScore)
  await user.type(homeScore, '73')
  await user.click(screen.getByRole('button', { name: 'Update Game' }))

  await waitFor(() =>
    expect(api.put).toHaveBeenCalledWith('/update-game/', {}, {
      params: {
        date: '2026-01-09',
        game_id: '1_2_2026-01-09',
        home_team: 'Northstar Academy',
        away_team: 'Cedar Valley',
        home_score: 73,
        away_score: 61,
        sport_type: 'basketball',
        gender: 'mens',
        level: 'high_school',
      },
    }),
  )
  expect(
    await screen.findByText('Updated Northstar Academy vs Cedar Valley on 2026-01-09'),
  ).toBeInTheDocument()
})

test('opens a flagged game with its dataset, teams, and scores preloaded', async () => {
  const user = userEvent.setup()
  const store = createStore(reducer)
  const flaggedIssue = {
    game_id: '1_2_2026-01-09',
    team1_id: 1,
    team2_id: 2,
    team1_name: 'Northstar Academy',
    team2_name: 'Cedar Valley',
    sport_type: 'football',
    gender: 'mens',
    level: 'college',
  }
  api.get.mockImplementation((url) => {
    if (url === '/teams-ids/') {
      return Promise.resolve({
        status: 200,
        data: {
          data: {
            teams: [
              { team_id: 1, team_name: 'Northstar Academy' },
              { team_id: 2, team_name: 'Cedar Valley' },
            ],
          },
        },
      })
    }

    return Promise.resolve({
      data: [{
        game_id: '1_2_2026-01-09',
        game_date: '2026-01-09',
        home_team_id: 1,
        home_team_name: 'Northstar Academy',
        away_team_id: 2,
        away_team_name: 'Cedar Valley',
        home_score: 72,
        away_score: 61,
      }],
    })
  })
  api.put.mockResolvedValue({
    data: { status: 200, message: 'Updated the flagged game' },
  })

  render(
    <Provider store={store}>
      <MemoryRouter initialEntries={[{
        pathname: '/admin/update_game',
        state: { flaggedIssue },
      }]}
      >
        <UpdateGame />
      </MemoryRouter>
    </Provider>,
  )

  expect(await screen.findByLabelText('Northstar Academy Score')).toHaveValue(72)
  expect(screen.getByLabelText('Cedar Valley Score')).toHaveValue(61)
  expect(screen.getByRole('button', { name: 'Update Game' })).toBeEnabled()
  expect(store.getState()).toMatchObject({ sport: 'football', gender: 'mens', level: 'college' })
  expect(api.get).toHaveBeenCalledWith('/season-dates/1/2', {
    params: { sport_type: 'football', gender: 'mens', level: 'college' },
  })

  await user.click(screen.getByRole('button', { name: 'Update Game' }))
  await waitFor(() => expect(api.put).toHaveBeenCalledWith('/update-game/', {}, {
    params: {
      date: '2026-01-09',
      game_id: '1_2_2026-01-09',
      home_team: 'Northstar Academy',
      away_team: 'Cedar Valley',
      home_score: 72,
      away_score: 61,
      sport_type: 'football',
      gender: 'mens',
      level: 'college',
    },
  }))
})
