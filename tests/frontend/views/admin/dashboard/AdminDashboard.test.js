import React from 'react'
import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Provider } from 'react-redux'
import { legacy_createStore as createStore } from 'redux'
import { MemoryRouter } from 'react-router-dom'
import api from 'src/api'
import AdminDashboard from 'src/views/admin/dashboard/AdminDashboard'

jest.mock('src/api', () => ({
  __esModule: true,
  default: {
    delete: jest.fn(),
    get: jest.fn(),
    post: jest.fn(),
  },
}))

const state = {
  sport: 'basketball',
  gender: 'mens',
  level: 'high_school',
}
const renderDashboard = () => render(
  <Provider store={createStore((currentState = state) => currentState)}>
    <MemoryRouter>
      <AdminDashboard />
    </MemoryRouter>
  </Provider>,
)

beforeEach(() => {
  api.delete.mockReset()
  api.get.mockReset()
  api.get.mockResolvedValue({ data: { z_scores: [] } })
  api.post.mockReset()
})

test('renders the dashboard links and season group', () => {
  renderDashboard()

  expect(screen.getByRole('heading', { name: 'PPR Admin Page' })).toBeInTheDocument()
  expect(screen.getByRole('heading', { name: 'Game' })).toBeInTheDocument()
  expect(screen.getByRole('heading', { name: 'Team' })).toBeInTheDocument()
  expect(screen.getByRole('heading', { name: 'Other' })).toBeInTheDocument()
  expect(screen.getByRole('heading', { name: 'Season' })).toBeInTheDocument()
  expect(screen.queryByRole('heading', { name: 'Calculate z Scores' })).not.toBeInTheDocument()
  expect(screen.queryByRole('button', { name: 'Calculate z Scores' })).not.toBeInTheDocument()
  expect(screen.queryByRole('heading', { name: 'Run Algorithm' })).not.toBeInTheDocument()
  expect(screen.queryByRole('button', { name: 'Run Algorithm' })).not.toBeInTheDocument()
  expect(screen.queryByRole('radio')).not.toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Archive Selected Sport' })).toHaveClass(
    'btn-outline-primary',
  )
  expect(screen.getByRole('button', { name: 'Archive All Sports' })).toHaveClass(
    'btn-outline-primary',
  )
  expect(screen.getByRole('button', { name: 'Reset Selected Sport' })).toHaveClass(
    'btn-outline-danger',
  )
  expect(screen.getByRole('button', { name: 'Reset All Sports' })).toHaveClass(
    'btn-outline-danger',
  )
  expect(screen.queryByRole('heading', { name: 'Algorithm Runs (Last 5)' })).not.toBeInTheDocument()

  const expectedLinks = [
    ['Add Games', '/admin/add_games'],
    ['Add Teams', '/admin/add_teams'],
    ['Export Teams', '/admin/export_teams'],
    ['Ranking', '/admin/ranking'],
    ['Z-Score', '/admin/z_scores'],
    ['Resolve Flagged Issues', '/admin/flagged-games'],
    ['Update Game', '/admin/update_game'],
    ['Update Team', '/admin/update_team'],
    ['Delete Game', '/admin/delete_game'],
    ['Delete Team', '/admin/delete_team'],
  ]
  expectedLinks.forEach(([name, href]) => {
    const link = screen.getByRole('link', { name })
    expect(link).toHaveAttribute('href', href)
    expect(link.closest('.col-md-4')).toBeInTheDocument()
  })
  expect(screen.queryByRole('link', { name: 'Update Team Name' })).not.toBeInTheDocument()
})

test('confirms an all-sports archive and displays a public archive link', async () => {
  const user = userEvent.setup()
  const year = new Date().getFullYear()
  api.get.mockResolvedValue({ data: { year, exists: false } })
  api.post.mockResolvedValue({
    data: { year, message: `Archived ${year} rankings` },
  })
  renderDashboard()

  await user.click(screen.getByRole('button', { name: 'Archive All Sports' }))

  expect(api.get).toHaveBeenCalledWith('/archive-season/status')
  const heading = await screen.findByRole('heading', {
    name: `Archive All Sports for ${year}?`,
  })
  const dialog = heading.closest('[role="dialog"]')

  await user.click(within(dialog).getByRole('button', { name: 'Archive All Sports' }))

  await waitFor(() => expect(api.post).toHaveBeenCalledWith('/archive-season/all/', {}, {
    params: { year, overwrite: false },
  }))
  expect(await screen.findByText(`Archived ${year} rankings`)).toBeInTheDocument()
  expect(screen.getByRole('link', { name: 'View archive' })).toHaveAttribute(
    'href',
    `/archives/${year}`,
  )
})

test('uses an explicit overwrite confirmation for an existing all-sports archive', async () => {
  const user = userEvent.setup()
  const year = new Date().getFullYear()
  api.get.mockResolvedValue({ data: { year, exists: true } })
  api.post.mockResolvedValue({ data: { year, message: `Archived ${year} rankings` } })
  renderDashboard()

  await user.click(screen.getByRole('button', { name: 'Archive All Sports' }))

  expect(
    await screen.findByRole('heading', { name: `Overwrite ${year} All Sports Archive?` }),
  ).toBeInTheDocument()
  expect(screen.getByText(/replace all of its static pages/i)).toBeInTheDocument()

  await user.click(screen.getByRole('button', { name: 'Overwrite All Sports Archive' }))

  await waitFor(() => expect(api.post).toHaveBeenCalledWith('/archive-season/all/', {}, {
    params: { year, overwrite: true },
  }))
})

test('archives only the selected sport dataset', async () => {
  const user = userEvent.setup()
  const year = new Date().getFullYear()
  api.get.mockResolvedValue({
    data: {
      year,
      exists: false,
      dataset: { label: 'College Womens Basketball' },
    },
  })
  api.post.mockResolvedValue({
    data: { year, message: `Archived ${year} College Womens Basketball rankings` },
  })
  renderDashboard()

  await user.click(screen.getByRole('button', { name: 'Archive Selected Sport' }))

  const dialog = await screen.findByRole('dialog')
  await user.selectOptions(within(dialog).getByLabelText('Gender'), 'womens')
  await user.selectOptions(within(dialog).getByLabelText('Level'), 'college')
  expect(within(dialog).getByRole('heading', {
    name: 'Archive College Womens Basketball?',
  })).toBeInTheDocument()

  await user.click(within(dialog).getByRole('button', { name: 'Archive Selected Sport' }))

  await waitFor(() => expect(api.get).toHaveBeenCalledWith(
    '/archive-season/status/selected',
    {
      params: {
        sport_type: 'basketball',
        gender: 'womens',
        level: 'college',
      },
    },
  ))
  expect(api.post).toHaveBeenCalledWith('/archive-season/selected/', {}, {
    params: {
      year,
      overwrite: false,
      sport_type: 'basketball',
      gender: 'womens',
      level: 'college',
    },
  })
  expect(
    await screen.findByText(`Archived ${year} College Womens Basketball rankings`),
  ).toBeInTheDocument()
})

test('requires overwrite confirmation only for the selected archived dataset', async () => {
  const user = userEvent.setup()
  api.get.mockResolvedValue({
    data: {
      year: 2026,
      exists: true,
      dataset: { label: 'High School Mens Basketball' },
    },
  })
  api.post.mockResolvedValue({ data: { year: 2026, message: 'Archive replaced' } })
  renderDashboard()

  await user.click(screen.getByRole('button', { name: 'Archive Selected Sport' }))
  const selectDialog = await screen.findByRole('dialog')
  await user.click(within(selectDialog).getByRole('button', {
    name: 'Archive Selected Sport',
  }))

  const overwriteHeading = await screen.findByRole('heading', {
    name: 'Overwrite 2026 High School Mens Basketball Archive?',
  })
  const overwriteDialog = overwriteHeading.closest('[role="dialog"]')
  expect(within(overwriteDialog).getByText(/preserve the other archived sports/i)).toBeInTheDocument()

  await user.click(within(overwriteDialog).getByRole('button', {
    name: 'Overwrite Selected Archive',
  }))
  await waitFor(() => expect(api.post).toHaveBeenCalledWith(
    '/archive-season/selected/',
    {},
    {
      params: {
        year: 2026,
        overwrite: true,
        sport_type: 'basketball',
        gender: 'mens',
        level: 'high_school',
      },
    },
  ))
})

test('confirms and clears only the selected season', async () => {
  const user = userEvent.setup()
  api.get.mockResolvedValue({ data: { year: 2026, exists: true } })
  api.delete.mockResolvedValue({ data: { return_data: 'Reset selected sport' } })
  renderDashboard()

  await user.click(screen.getByRole('button', { name: 'Reset Selected Sport' }))

  const dialog = await screen.findByRole('dialog')
  expect(api.get).not.toHaveBeenCalledWith('/archive-season/status/selected', expect.anything())
  expect(within(dialog).getByRole('heading', {
    name: 'Reset High School Mens Basketball Season?',
  })).toBeInTheDocument()
  expect(within(dialog).getByLabelText('Sport')).toHaveValue('basketball')
  expect(within(dialog).getByLabelText('Gender')).toHaveValue('mens')
  expect(within(dialog).getByLabelText('Level')).toHaveValue('high_school')
  expect(within(dialog).getByText(/ranking values and each team's five most recent/i))
    .toBeInTheDocument()
  expect(within(dialog).getByText(/cannot be undone/i)).toBeInTheDocument()
  expect(api.delete).not.toHaveBeenCalled()

  await user.selectOptions(within(dialog).getByLabelText('Gender'), 'womens')
  await user.selectOptions(within(dialog).getByLabelText('Level'), 'college')

  expect(within(dialog).getByRole('heading', {
    name: 'Reset College Womens Basketball Season?',
  })).toBeInTheDocument()

  await user.click(within(dialog).getByRole('button', { name: 'Reset Selected Sport' }))

  await waitFor(() => expect(api.get).toHaveBeenCalledWith(
    '/archive-season/status/selected',
    {
      params: {
        sport_type: 'basketball',
        gender: 'womens',
        level: 'college',
      },
    },
  ))
  await waitFor(() => expect(api.delete).toHaveBeenCalledWith('/clear-season/', {
    params: {
      sport_type: 'basketball',
      gender: 'womens',
      level: 'college',
    },
  }))
  expect(await screen.findByText('Reset selected sport')).toBeInTheDocument()
})

test('requires confirmation before resetting all sports', async () => {
  const user = userEvent.setup()
  api.get.mockResolvedValue({ data: { year: 2026, exists: true, complete: true } })
  api.delete.mockResolvedValue({
    data: { return_data: 'Reset 6 sports datasets' },
  })
  renderDashboard()

  await user.click(screen.getByRole('button', { name: 'Reset All Sports' }))

  const dialog = await screen.findByRole('dialog')
  expect(api.get).toHaveBeenCalledWith('/archive-season/status')
  expect(within(dialog).getByRole('heading', {
    name: 'Reset All Sports?',
  })).toBeInTheDocument()
  expect(within(dialog).getByText(/action cannot be undone/i)).toBeInTheDocument()
  expect(api.delete).not.toHaveBeenCalled()

  await user.click(within(dialog).getByRole('button', { name: 'Reset All Sports' }))

  await waitFor(() => expect(api.delete).toHaveBeenCalledWith('/reset-all-sports/'))
  expect(await screen.findByText('Reset 6 sports datasets')).toBeInTheDocument()
})

test('warns before resetting a selected sport that is not archived', async () => {
  const user = userEvent.setup()
  api.get.mockResolvedValue({ data: { year: 2026, exists: false } })
  api.delete.mockResolvedValue({ data: { return_data: 'Reset complete' } })
  renderDashboard()

  await user.click(screen.getByRole('button', { name: 'Reset Selected Sport' }))
  const resetDialog = await screen.findByRole('dialog')
  await user.click(within(resetDialog).getByRole('button', {
    name: 'Reset Selected Sport',
  }))

  const warningDialog = await screen.findByRole('dialog')
  expect(within(warningDialog).getByRole('heading', {
    name: '2026 High School Mens Basketball Is Not Archived',
  })).toBeInTheDocument()
  expect(within(warningDialog).getByText(
    /permanently remove the current High School Mens Basketball data/i,
  )).toBeInTheDocument()
  expect(api.delete).not.toHaveBeenCalled()

  await user.click(within(warningDialog).getByRole('button', {
    name: 'Proceed Without Archiving',
  }))

  await waitFor(() => expect(api.delete).toHaveBeenCalledWith('/clear-season/', {
    params: {
      sport_type: 'basketball',
      gender: 'mens',
      level: 'high_school',
    },
  }))
})

test('warns before resetting all sports without a complete archive', async () => {
  const user = userEvent.setup()
  api.get.mockResolvedValue({ data: { year: 2026, exists: true, complete: false } })
  api.delete.mockResolvedValue({ data: { return_data: 'Reset complete' } })
  renderDashboard()

  await user.click(screen.getByRole('button', { name: 'Reset All Sports' }))

  const warningDialog = await screen.findByRole('dialog')
  expect(within(warningDialog).getByRole('heading', {
    name: '2026 Complete Season Is Not Archived',
  })).toBeInTheDocument()
  expect(within(warningDialog).getByText(/without a complete all-sports archive/i))
    .toBeInTheDocument()
  expect(api.delete).not.toHaveBeenCalled()

  await user.click(within(warningDialog).getByRole('button', {
    name: 'Proceed Without Archiving',
  }))

  const confirmation = await screen.findByRole('heading', { name: 'Reset All Sports?' })
  const confirmationDialog = confirmation.closest('[role="dialog"]')
  await user.click(within(confirmationDialog).getByRole('button', {
    name: 'Reset All Sports',
  }))
  await waitFor(() => expect(api.delete).toHaveBeenCalledWith('/reset-all-sports/'))
})
