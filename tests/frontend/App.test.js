import React from 'react'
import { render, screen } from '@testing-library/react'
import { Provider } from 'react-redux'
import App from 'src/App'
import { store } from 'src/store'

const renderApp = () =>
  render(
    <Provider store={store}>
      <App />
    </Provider>,
  )

beforeEach(() => {
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
    '/teams/football/mens/college',
  )
  expect(screen.getByRole('link', { name: /womens high school basketball/i })).toHaveAttribute(
    'href',
    '/teams/basketball/womens/high_school',
  )
  expect(screen.getByRole('link', { name: /season archives/i })).toHaveAttribute(
    'href',
    '/archives',
  )
})

test('redirects a signed-out visitor from an admin route to the admin login', async () => {
  window.history.pushState({}, '', '/admin/ranking')
  renderApp()

  expect(await screen.findByRole('heading', { name: /admin login/i })).toBeInTheDocument()
  expect(window.location.pathname).toBe('/admin/login')
})
