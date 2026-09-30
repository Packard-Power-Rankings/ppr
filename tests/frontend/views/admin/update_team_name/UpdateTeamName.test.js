import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Provider } from 'react-redux'
import { legacy_createStore as createStore } from 'redux'
import api from 'src/api'
import UpdateTeamName from 'src/views/admin/update_team_name/UpdateTeamName'

jest.mock('src/api', () => ({
  __esModule: true,
  default: {
    get: jest.fn(),
    put: jest.fn(),
  },
}))

const initialState = {
  sport: 'basketball',
  gender: 'mens',
  level: 'high_school',
}

const reducer = (state = initialState) => state

beforeEach(() => {
  api.get.mockReset()
  api.put.mockReset()
})

test('asks for confirmation before updating every instance of a team name', async () => {
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
  api.put.mockResolvedValue({
    data: {
      status: 200,
      message: 'Northstar Academy was renamed to Northstar Prep',
    },
  })

  render(
    <Provider store={store}>
      <UpdateTeamName />
    </Provider>,
  )

  await user.click(await screen.findByRole('combobox', { name: 'Current Team Name' }))
  await user.click(await screen.findByText('Northstar Academy'))
  await user.type(screen.getByLabelText('New Team Name'), '  Northstar Prep  ')
  await user.click(screen.getByRole('button', { name: 'Update Team Name' }))

  expect(api.put).not.toHaveBeenCalled()
  expect(
    screen.getByRole('heading', { name: 'Confirm Team Name Update' }),
  ).toBeInTheDocument()
  expect(
    screen.getByText(/All instances of the current team name will be updated/),
  ).toBeInTheDocument()

  await user.click(screen.getByRole('button', { name: 'Confirm Update' }))

  await waitFor(() =>
    expect(api.put).toHaveBeenCalledWith('/update-name/12/Northstar%20Prep', {}, {
      params: {
        sport_type: 'basketball',
        gender: 'mens',
        level: 'high_school',
      },
    }),
  )
  expect(
    await screen.findByText('Northstar Academy was renamed to Northstar Prep'),
  ).toBeInTheDocument()
})
