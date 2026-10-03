import React from 'react'
import { render, screen } from '@testing-library/react'
import { Provider } from 'react-redux'
import { legacy_createStore as createStore } from 'redux'
import { MemoryRouter } from 'react-router-dom'
import DefaultLayout from 'src/layout/DefaultLayout'

jest.mock('src/components/index', () => ({
  AppContent: () => null,
  AppSidebar: () => null,
  AppFooter: () => null,
  AppHeader: () => null,
  AdminHeader: jest.requireActual('src/components/AdminHeader').default,
}))

const renderLayout = (path) => render(
  <Provider store={createStore(() => ({
    isAdmin: true,
    authReady: true,
    sport: 'basketball',
    gender: 'mens',
    level: 'high_school',
  }))}>
    <MemoryRouter initialEntries={[path]}>
      <DefaultLayout />
    </MemoryRouter>
  </Provider>,
)

test('hides admin dataset selectors on flagged issues while retaining them on update pages', () => {
  const { unmount } = renderLayout('/admin/flagged-games')

  expect(screen.queryByRole('combobox', { name: 'Sport' })).not.toBeInTheDocument()
  expect(screen.queryByRole('combobox', { name: 'Gender' })).not.toBeInTheDocument()
  expect(screen.queryByRole('combobox', { name: 'Level' })).not.toBeInTheDocument()

  unmount()
  renderLayout('/admin/update_game')

  expect(screen.getByRole('combobox', { name: 'Sport' })).toBeInTheDocument()
  expect(screen.getByRole('combobox', { name: 'Gender' })).toBeInTheDocument()
  expect(screen.getByRole('combobox', { name: 'Level' })).toBeInTheDocument()
})