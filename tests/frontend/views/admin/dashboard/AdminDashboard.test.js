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
  api.post.mockReset()
})

test('renders the dashboard links and season group', () => {
  renderDashboard()

  expect(screen.getByRole('heading', { name: 'PPR Admin Page' })).toBeInTheDocument()
  expect(screen.getByRole('heading', { name: 'Season' })).toBeInTheDocument()
  expect(screen.getByText('High School Mens Basketball')).toBeInTheDocument()

  const expectedLinks = [
    ['Add Teams', '/admin/add_teams'],
    ['Rankings', '/admin/ranking'],
    ['Update Game', '/admin/update_game'],
    ['Update Team Name', '/admin/update_team_name'],
    ['Delete Game', '/admin/delete_game'],
    ['Delete Team', '/admin/delete_team'],
  ]
  expectedLinks.forEach(([name, href]) => {
    expect(screen.getByRole('link', { name })).toHaveAttribute('href', href)
  })
})

test('confirms a new archive and displays a public archive link', async () => {
  const user = userEvent.setup()
  const year = new Date().getFullYear()
  api.get.mockResolvedValue({ data: { year, exists: false } })
  api.post.mockResolvedValue({
    data: { year, message: `Archived ${year} rankings` },
  })
  renderDashboard()

  await user.click(screen.getByRole('button', { name: 'Archive Season' }))

  expect(api.get).toHaveBeenCalledWith('/archive-season/status')
  expect(
    await screen.findByRole('heading', { name: `Archive ${year} Season?` }),
  ).toBeInTheDocument()

  await user.click(screen.getByRole('button', { name: 'Create Archive' }))

  await waitFor(() => expect(api.post).toHaveBeenCalledWith('/archive-season/', {}, {
    params: { year, overwrite: false },
  }))
  expect(await screen.findByText(`Archived ${year} rankings`)).toBeInTheDocument()
  expect(screen.getByRole('link', { name: 'View archive' })).toHaveAttribute(
    'href',
    `/archives/${year}`,
  )
})

test('uses an explicit overwrite confirmation for an existing archive', async () => {
  const user = userEvent.setup()
  const year = new Date().getFullYear()
  api.get.mockResolvedValue({ data: { year, exists: true } })
  api.post.mockResolvedValue({ data: { year, message: `Archived ${year} rankings` } })
  renderDashboard()

  await user.click(screen.getByRole('button', { name: 'Archive Season' }))

  expect(
    await screen.findByRole('heading', { name: `Overwrite ${year} Archive?` }),
  ).toBeInTheDocument()
  expect(screen.getByText(/replace its static pages with the current rankings/i)).toBeInTheDocument()

  await user.click(screen.getByRole('button', { name: 'Overwrite Archive' }))

  await waitFor(() => expect(api.post).toHaveBeenCalledWith('/archive-season/', {}, {
    params: { year, overwrite: true },
  }))
})

test('confirms and clears only the selected season', async () => {
  const user = userEvent.setup()
  api.delete.mockResolvedValue({ data: { return_data: 'Cleared season' } })
  renderDashboard()

  await user.click(screen.getByRole('button', { name: 'Clear Season' }))

  const dialog = await screen.findByRole('dialog')
  expect(within(dialog).getByRole('heading', {
    name: 'Clear High School Mens Basketball Season?',
  })).toBeInTheDocument()
  expect(within(dialog).getByText(/cannot be undone/i)).toBeInTheDocument()
  expect(api.delete).not.toHaveBeenCalled()

  await user.click(within(dialog).getByRole('button', { name: 'Clear Season' }))

  await waitFor(() => expect(api.delete).toHaveBeenCalledWith('/clear-season/', {
    params: {
      sport_type: 'basketball',
      gender: 'mens',
      level: 'high_school',
    },
  }))
  expect(await screen.findByText('Cleared season')).toBeInTheDocument()
})
