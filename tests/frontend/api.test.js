import React, { useEffect } from 'react'
import { AxiosError } from 'axios'
import { Provider } from 'react-redux'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { render, screen } from '@testing-library/react'
import api from 'src/api'
import RequireAdmin from 'src/components/RequireAdmin'
import { store } from 'src/store'

const originalAdapter = api.defaults.adapter

const rejectUnauthorized = (config) => Promise.reject(new AxiosError(
  'Unauthorized',
  AxiosError.ERR_BAD_REQUEST,
  config,
  null,
  {
    data: {},
    status: 401,
    statusText: 'Unauthorized',
    headers: {},
    config,
  },
))

const ExpiredSessionPage = () => {
  useEffect(() => {
    api.get('/protected-data/').catch(() => {})
  }, [])

  return <div>Protected Admin Page</div>
}

beforeEach(() => {
  store.dispatch({ type: 'logout' })
  api.defaults.adapter = rejectUnauthorized
})

afterEach(() => {
  api.defaults.adapter = originalAdapter
})

test('redirects an admin to login when an authenticated request returns 401', async () => {
  store.dispatch({ type: 'login' })

  render(
    <Provider store={store}>
      <MemoryRouter initialEntries={['/admin/protected']}>
        <Routes>
          <Route
            path="/admin/protected"
            element={<RequireAdmin><ExpiredSessionPage /></RequireAdmin>}
          />
          <Route path="/admin/login" element={<h1>Admin Login</h1>} />
        </Routes>
      </MemoryRouter>
    </Provider>,
  )

  expect(await screen.findByRole('heading', { name: 'Admin Login' })).toBeInTheDocument()
  expect(store.getState().isAdmin).toBe(false)
})

test('does not clear an existing session after a login request returns 401', async () => {
  store.dispatch({ type: 'login' })

  await expect(api.post('/token/')).rejects.toMatchObject({
    response: { status: 401 },
  })

  expect(store.getState().isAdmin).toBe(true)
})

test('sends credentials so the browser can use the HttpOnly admin cookie', () => {
  expect(api.defaults.withCredentials).toBe(true)
})
