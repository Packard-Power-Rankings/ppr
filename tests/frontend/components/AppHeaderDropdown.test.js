import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Provider } from 'react-redux'
import { legacy_createStore as createStore } from 'redux'
import { MemoryRouter, useLocation } from 'react-router-dom'

import api from 'src/api'
import AppHeaderDropdown from 'src/components/header/AppHeaderDropdown'

jest.mock('src/api', () => ({
  __esModule: true,
  default: { get: jest.fn() },
}))

jest.mock('src/services/authService', () => ({
  logoutUser: jest.fn(),
}))

const LocationDisplay = () => {
  const location = useLocation()
  return <div data-testid="location">{location.pathname}</div>
}

const renderDropdown = (state) => render(
  <Provider store={createStore((currentState = state) => currentState)}>
    <MemoryRouter>
      <AppHeaderDropdown />
      <LocationDisplay />
    </MemoryRouter>
  </Provider>,
)

beforeEach(() => {
  api.get.mockReset()
})

test('shows the unresolved issue count on the admin shield and links to review', async () => {
  const user = userEvent.setup()
  api.get.mockResolvedValue({ data: { count: 3 } })
  renderDropdown({ isAdmin: true, authReady: true })

  const adminMenu = await screen.findByRole('button', {
    name: 'Admin menu, 3 unresolved game issues',
  })
  expect(screen.getByText('3')).toBeInTheDocument()
  expect(api.get).toHaveBeenCalledWith('/flagged-games/count')

  await user.click(adminMenu)
  await user.click(await screen.findByRole('button', { name: 'Flagged Issues (3)' }))
  await waitFor(() => expect(screen.getByTestId('location')).toHaveTextContent(
    '/admin/flagged-games',
  ))
})

test('does not request or display issue counts for a signed-out visitor', () => {
  renderDropdown({ isAdmin: false, authReady: true })

  expect(screen.getByRole('button', { name: 'Admin menu' })).toBeInTheDocument()
  expect(api.get).not.toHaveBeenCalled()
})
