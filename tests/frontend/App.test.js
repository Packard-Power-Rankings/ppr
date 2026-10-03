import React from 'react'
import { render, screen } from '@testing-library/react'
import { Provider } from 'react-redux'
import App from 'src/App'
import api from 'src/api'
import { store } from 'src/store'

jest.mock('src/api', () => ({
  __esModule: true,
  default: { get: jest.fn() },
}))

jest.mock('src/services/authService', () => ({
  initializeAuth: jest.fn(),
}))

const renderApp = () =>
  render(
    <Provider store={store}>
      <App />
    </Provider>,
  )

beforeEach(() => {
  api.get.mockReset()
  api.get.mockResolvedValue({ data: { count: 0 } })
  localStorage.clear()
  store.dispatch({ type: 'logout' })
})

test('renders the public application at the root URL', async () => {
  window.history.pushState({}, '', '/')
  renderApp()

  expect(
    await screen.findByRole(
      'heading',
      { name: /welcome to packard power rankings/i },
      { timeout: 3000 },
    ),
  ).toBeInTheDocument()
  expect(screen.getByRole('link', { name: /mens college football/i })).toHaveAttribute(
    'href',
    '/football/mens/college',
  )
  expect(screen.getByRole('link', { name: /womens high school basketball/i })).toHaveAttribute(
    'href',
    '/basketball/womens/high_school',
  )
  expect(screen.getByRole('link', { name: /season archives/i })).toHaveAttribute(
    'href',
    '/archives',
  )
  expect(screen.queryByRole('link', { name: /view all teams/i })).not.toBeInTheDocument()
  expect(screen.getByRole('heading', {
    name: 'Current Rankings',
  })).toBeInTheDocument()
  expect(screen.getByRole('navigation', { name: 'Current Football rankings' })).toBeInTheDocument()
})

test('redirects a signed-out visitor from an admin route to the admin login', async () => {
  window.history.pushState({}, '', '/admin/ranking')
  renderApp()

  expect(await screen.findByRole('heading', { name: /admin login/i })).toBeInTheDocument()
  expect(window.location.pathname).toBe('/admin/login')
})

test('does not display the global dataset selectors on the admin dashboard', async () => {
  store.dispatch({ type: 'login' })
  window.history.pushState({}, '', '/admin')
  renderApp()

  expect(await screen.findByRole('heading', { name: /ppr admin page/i })).toBeInTheDocument()
  expect(screen.queryByRole('radio')).not.toBeInTheDocument()
})

test('redirects a legacy Site Info URL to its shorter public URL', async () => {
  window.history.pushState({}, '', '/info/privacy')
  renderApp()

  expect(await screen.findByRole('heading', { name: /privacy policy/i })).toBeInTheDocument()
  expect(window.location.pathname).toBe('/privacy')
})

test('redirects the retired all-teams page to home', async () => {
  window.history.pushState({}, '', '/teams')
  renderApp()

  expect(
    await screen.findByRole('heading', { name: /welcome to packard power rankings/i }),
  ).toBeInTheDocument()
  expect(window.location.pathname).toBe('/')
})
