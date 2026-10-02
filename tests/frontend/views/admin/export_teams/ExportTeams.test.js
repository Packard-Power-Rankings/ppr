import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Provider } from 'react-redux'
import { legacy_createStore as createStore } from 'redux'
import api from 'src/api'
import AdminHeader from 'src/components/AdminHeader'
import ExportTeams from 'src/views/admin/export_teams/ExportTeams'

jest.mock('src/api', () => ({
  __esModule: true,
  default: {
    get: jest.fn(),
  },
}))

const originalCreateObjectURL = URL.createObjectURL
const originalRevokeObjectURL = URL.revokeObjectURL
let clickLink

beforeEach(() => {
  api.get.mockReset()
})

afterEach(() => {
  clickLink?.mockRestore()
  if (originalCreateObjectURL) {
    Object.defineProperty(URL, 'createObjectURL', { configurable: true, value: originalCreateObjectURL })
  } else {
    delete URL.createObjectURL
  }
  if (originalRevokeObjectURL) {
    Object.defineProperty(URL, 'revokeObjectURL', { configurable: true, value: originalRevokeObjectURL })
  } else {
    delete URL.revokeObjectURL
  }
})

test('exports all selected team fields and additional database fields with headers', async () => {
  const user = userEvent.setup()
  const store = createStore((state = {
    sport: 'basketball',
    gender: 'womens',
    level: 'college',
  }, action) => (action.type === 'updateAdminState'
    ? { ...state, ...action.payload }
    : state))
  const createObjectURL = jest.fn(() => 'blob:team-export')
  const revokeObjectURL = jest.fn()
  Object.defineProperty(URL, 'createObjectURL', { configurable: true, value: createObjectURL })
  Object.defineProperty(URL, 'revokeObjectURL', { configurable: true, value: revokeObjectURL })
  clickLink = jest.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {})
  api.get.mockResolvedValue({
    data: {
      teams: [{
        team_id: 7,
        overall_rank: 3,
        last_rank: 4,
        team_name: 'Northstar Academy',
        short_name: 'N. Academy',
        long_name: 'Northstar Academy',
        state: 'CA',
        power_ranking: [{ initial: 50 }, { '2026-10-01': 55.5 }],
        division: '5A',
        division_rank: 1,
        conference: 'Western',
        conference_rank: 2,
        wins: 8,
        losses: 2,
        ties: 1,
        ranked: true,
        date: '2026-10-01',
        recent_opp: [11, 12, 0, 0, 0],
        season_opp: [
          { opponent_id: 11, opponent_name: 'Older Team', game_date: '2026-09-01' },
          { opponent_id: 12, opponent_name: 'Newer Team', game_date: '2026-10-01' },
        ],
        custom_stats: { playoff_wins: 3 },
      }],
    },
  })

  render(
    <Provider store={store}>
      <AdminHeader />
      <ExportTeams />
    </Provider>,
  )

  expect(screen.getByRole('heading', { name: 'Export Teams' })).toBeInTheDocument()
  expect(screen.getAllByRole('combobox')).toHaveLength(3)
  await user.selectOptions(screen.getByLabelText('Sport'), 'football')
  await user.selectOptions(screen.getByLabelText('Level'), 'high_school')
  expect(screen.getByRole('combobox', { name: 'Gender' })).toHaveValue('mens')
  await user.click(screen.getByRole('button', { name: 'Selected Teams only as CSV' }))

  await waitFor(() => expect(api.get).toHaveBeenCalledWith('/export_teams/', {
    params: { sport_type: 'football', gender: 'mens', level: 'high_school' },
  }))
  const exportedBlob = createObjectURL.mock.calls[0][0]
  const csv = await new Promise((resolve) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result)
    reader.readAsText(exportedBlob)
  })

  expect(csv).toContain('"Team ID","Current Rank","Last Rank","Short Name","Long Name","State","Power Rank","Div","Div Rank","Conference","Conf. Rank","Total Wins","Total Loss","Total Ties","Ranked"')
  expect(csv).toContain('"Northstar Academy (N. Academy)"')
  expect(csv).not.toContain('"Date"')
  expect(csv).not.toContain('"Team Name"')
  expect(csv).toContain('"55.5"')
  expect(csv).not.toContain('"[{""initial"":50},{""2026-10-01"":55.5}]"')
  expect(csv).toContain('Custom Stats')
  expect(csv).toContain('Recent Opp IDs')
  expect(csv).not.toContain('"Recent Opp"')
  expect(csv).not.toContain('Newer Team')
  expect(csv).not.toContain('Older Team')
  expect(clickLink).toHaveBeenCalledTimes(1)
  expect(revokeObjectURL).toHaveBeenCalledWith('blob:team-export')
  expect(await screen.findByRole('status')).toHaveTextContent('Exported 1 teams to CSV.')
})