import React from 'react'
import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Provider } from 'react-redux'
import { legacy_createStore as createStore } from 'redux'
import { MemoryRouter } from 'react-router-dom'
import api from 'src/api'
import ImportPreviousSeason from 'src/views/admin/import_previous_season/ImportPreviousSeason'

jest.mock('src/api', () => ({
  __esModule: true,
  default: { post: jest.fn() },
}))

const renderPage = () => render(
  <Provider store={createStore((state = {
    sport: 'basketball',
    gender: 'womens',
    level: 'college',
  }) => state)}>
    <MemoryRouter>
      <ImportPreviousSeason />
    </MemoryRouter>
  </Provider>,
)

beforeEach(() => api.post.mockReset())

test('confirms the import and displays unmatched short names', async () => {
  const user = userEvent.setup()
  api.post.mockResolvedValue({
    data: {
      message: 'Imported previous-season rankings for 1 of 2 rows; flagged 1.',
      source_filename: 'WomensCollegeBasketball.csv',
      teams_updated_count: 1,
      teams_flagged_count: 1,
      flagged_teams: [{
        row: 3,
        team_id: 'Missing Team',
        reason: 'No existing team has this short_name',
      }],
      warnings: [],
    },
  })
  renderPage()

  const file = new File(['team_id,wins,losses,ties,power,overall_rank,recent_opponent_1,recent_opponent_2,recent_opponent_3,recent_opponent_4,recent_opponent_5,div_rank\nUCLA,37,1,0,425.5,1,0,0,0,0,0,1'], 'WomensCollegeBasketball.csv', {
    type: 'text/csv',
  })
  await user.upload(screen.getByLabelText('Choose Final Season Ranking CSV'), file)
  await user.click(screen.getByRole('button', { name: 'Review Import' }))

  const dialog = await screen.findByRole('dialog')
  expect(within(dialog).getByRole('heading', {
    name: 'Import College Womens Basketball Final Rankings?',
  })).toBeInTheDocument()
  expect(within(dialog).getByText(/will be flagged and skipped/i)).toBeInTheDocument()

  await user.click(within(dialog).getByRole('button', {
    name: 'Import Previous Season',
  }))

  await waitFor(() => expect(api.post).toHaveBeenCalledWith(
    '/previous-season/import/',
    expect.any(FormData),
    {
      params: {
        sport_type: 'basketball',
        gender: 'womens',
        level: 'college',
      },
    },
  ))
  expect(await screen.findByText('Missing Team')).toBeInTheDocument()
  expect(screen.getByText('No existing team has this short_name')).toBeInTheDocument()
  expect(screen.getByRole('link', { name: 'Continue To Archive And Reset' }))
    .toHaveAttribute('href', '/admin')
})

const importFile = async (user) => {
  const file = new File(['team_id,wins\nUCLA,37'], 'WomensCollegeBasketball.csv', {
    type: 'text/csv',
  })
  await user.upload(screen.getByLabelText('Choose Final Season Ranking CSV'), file)
  await user.click(screen.getByRole('button', { name: 'Review Import' }))
  const dialog = await screen.findByRole('dialog')
  await user.click(within(dialog).getByRole('button', {
    name: 'Import Previous Season',
  }))
}

const mockImport = (overrides) => api.post.mockResolvedValue({
  data: {
    message: 'Imported previous-season rankings.',
    source_filename: 'WomensCollegeBasketball.csv',
    teams_updated_count: 2,
    teams_flagged_count: 0,
    flagged_teams: [],
    warnings: [],
    ...overrides,
  },
})

const feedbackAlert = async (message) => (await screen.findByText(message)).closest('.alert')

test('shows a success alert without next steps for a clean import', async () => {
  const user = userEvent.setup()
  const message = 'Imported previous-season rankings for 2 of 2 rows; flagged 0.'
  mockImport({ message })
  renderPage()
  await importFile(user)

  expect(await feedbackAlert(message)).toHaveClass('alert-success')
  expect(screen.queryByRole('heading', { name: 'Action Needed' })).not.toBeInTheDocument()
})

test('shows a warning alert and next steps when there are only warnings', async () => {
  const user = userEvent.setup()
  const message = 'Imported previous-season rankings for 2 of 2 rows; flagged 0.'
  mockImport({
    message,
    warnings: [{
      row: 2,
      team_id: 'UCLA',
      reason: 'Unknown recent opponent IDs were replaced with 0: 99',
    }],
  })
  renderPage()
  await importFile(user)

  expect(await feedbackAlert(message)).toHaveClass('alert-warning')
  const actions = screen.getByRole('heading', { name: 'Action Needed' }).closest('.alert')
  expect(within(actions).getByText(/correct the recent opponent IDs/i)).toBeInTheDocument()
  expect(within(actions).queryByText(/legacy team ID/i)).not.toBeInTheDocument()
  expect(within(actions).getByText(/Import the corrected file again/i)).toBeInTheDocument()
  expect(within(actions).getByRole('link', { name: 'Add Teams' }))
    .toHaveAttribute('href', '/admin/add_teams')
})

test('shows a warning alert and next steps when rows are flagged', async () => {
  const user = userEvent.setup()
  const message = 'Imported previous-season rankings for 1 of 2 rows; flagged 1.'
  mockImport({
    message,
    teams_updated_count: 1,
    teams_flagged_count: 1,
    flagged_teams: [{ row: 3, team_id: 'Missing Team', reason: 'No match' }],
  })
  renderPage()
  await importFile(user)

  expect(await feedbackAlert(message)).toHaveClass('alert-warning')
  const actions = screen.getByRole('heading', { name: 'Action Needed' }).closest('.alert')
  expect(within(actions).getByText(/legacy team ID match exactly one/i)).toBeInTheDocument()
  expect(within(actions).queryByText(/recent opponent IDs/i)).not.toBeInTheDocument()
  expect(within(actions).getByRole('link', { name: 'Update Team' }))
    .toHaveAttribute('href', '/admin/update_team')
})
