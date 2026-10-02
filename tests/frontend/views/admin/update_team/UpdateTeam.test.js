import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Provider } from 'react-redux'
import { legacy_createStore as createStore } from 'redux'
import api from 'src/api'
import UpdateTeam from 'src/views/admin/update_team/UpdateTeam'

jest.mock('src/api', () => ({
  __esModule: true,
  default: {
    get: jest.fn(),
    put: jest.fn(),
  },
}))

const state = {
  sport: 'basketball',
  gender: 'mens',
  level: 'high_school',
}

const renderUpdateTeam = () => render(
  <Provider store={createStore((currentState = state) => currentState)}>
    <UpdateTeam />
  </Provider>,
)

beforeEach(() => {
  api.get.mockReset()
  api.put.mockReset()
})

test('loads a searchable team and saves edited team information', async () => {
  const user = userEvent.setup()
  api.get.mockResolvedValue({
    status: 200,
    data: {
      data: {
        teams: [{
          team_id: 12,
          team_name: 'Northstar Academy',
          short_name: 'Northstar Academy',
          long_name: 'Northstar Academy',
          state: 'Oregon',
          division: '5A',
          conference: 'West',
          ranked: true,
        }],
      },
    },
  })
  api.put.mockResolvedValue({
    data: { status: 200, message: 'Updated Northstar Academy information' },
  })

  renderUpdateTeam()

  await user.click(await screen.findByRole('combobox', { name: 'Search Team' }))
  await user.click(screen.getByText('Northstar Academy'))
  expect(screen.getByLabelText('Division')).toHaveValue('5A')
  expect(screen.getByLabelText('State')).toHaveValue('Oregon')

  await user.clear(screen.getByLabelText('Division'))
  await user.type(screen.getByLabelText('Division'), '4A')
  await user.selectOptions(screen.getByLabelText('State'), 'Washington')
  await user.selectOptions(screen.getByLabelText('Ranked'), 'false')
  await user.click(screen.getByRole('button', { name: 'Save Team Information' }))
  await user.click(await screen.findByRole('button', { name: 'Confirm Update' }))

  await waitFor(() => expect(api.put).toHaveBeenCalledWith(
    '/update-team/12',
    {
      short_name: 'Northstar Academy',
      long_name: 'Northstar Academy',
      state: 'Washington',
      division: '4A',
      conference: 'West',
      ranked: false,
    },
    { params: { sport_type: state.sport, gender: state.gender, level: state.level } },
  ))
  expect(await screen.findByText('Updated Northstar Academy information')).toBeInTheDocument()
})