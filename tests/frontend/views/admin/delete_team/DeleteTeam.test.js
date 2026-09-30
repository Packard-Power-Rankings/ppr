import React from 'react'
import { act, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Provider } from 'react-redux'
import { legacy_createStore as createStore } from 'redux'
import api from 'src/api'
import DeleteTeam from 'src/views/admin/delete_team/DeleteTeam'

jest.mock('src/api', () => ({
  __esModule: true,
  default: {
    delete: jest.fn(),
    get: jest.fn(),
  },
}))

const initialState = {
  sport: 'football',
  gender: 'mens',
  level: 'high_school',
}

const reducer = (state = initialState, action) =>
  action.type === 'selectDataset' ? { ...state, ...action.payload } : state

beforeEach(() => {
  api.get.mockReset()
  api.delete.mockReset()
})

test('reloads team options when the selected admin dataset changes', async () => {
  const user = userEvent.setup()
  const store = createStore(reducer)

  api.get.mockImplementation((_url, { params }) => {
    if (params.sport_type === 'basketball') {
      return Promise.resolve({
        status: 200,
        data: {
          status: 200,
          data: {
            teams: [{ team_id: 1, team_name: 'Northstar Academy' }],
          },
        },
      })
    }

    return Promise.resolve({ status: 200, data: { status: 204, data: null } })
  })

  render(
    <Provider store={store}>
      <DeleteTeam />
    </Provider>,
  )

  await waitFor(() => expect(api.get).toHaveBeenCalledTimes(1))

  act(() => {
    store.dispatch({ type: 'selectDataset', payload: { sport: 'basketball' } })
  })

  await waitFor(() =>
    expect(api.get).toHaveBeenLastCalledWith('/teams-ids/', {
      params: {
        sport_type: 'basketball',
        gender: 'mens',
        level: 'high_school',
      },
    }),
  )

  await user.click(screen.getByRole('combobox'))
  expect(await screen.findByText('Northstar Academy')).toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Delete Team' })).toBeInTheDocument()
})

test('requires confirmation before deleting a team and its games', async () => {
  const user = userEvent.setup()
  const store = createStore(reducer)

  api.get.mockResolvedValue({
    status: 200,
    data: {
      status: 200,
      data: {
        teams: [{ team_id: 12, team_name: 'Northstar Academy' }],
      },
    },
  })
  api.delete.mockResolvedValue({
    data: {
      status: 200,
      message: 'Northstar Academy and related game data were deleted',
    },
  })

  render(
    <Provider store={store}>
      <DeleteTeam />
    </Provider>,
  )

  await user.click(await screen.findByRole('combobox'))
  await user.click(await screen.findByText('Northstar Academy'))
  await user.click(screen.getByRole('button', { name: 'Delete Team' }))

  expect(api.delete).not.toHaveBeenCalled()
  expect(screen.getByRole('heading', { name: 'Delete Team?' })).toBeInTheDocument()
  expect(
    screen.getByText(/All team and game-related information will be deleted/),
  ).toBeInTheDocument()

  await user.click(screen.getByRole('button', { name: 'Confirm Delete Team' }))

  await waitFor(() =>
    expect(api.delete).toHaveBeenCalledWith('/delete-team/Northstar%20Academy/12/', {
      params: {
        sport_type: 'football',
        gender: 'mens',
        level: 'high_school',
      },
    }),
  )
  expect(
    await screen.findByText('Northstar Academy and related game data were deleted'),
  ).toBeInTheDocument()
})
