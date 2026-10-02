import React from 'react'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Provider } from 'react-redux'
import { legacy_createStore as createStore } from 'redux'
import AdminHeader from 'src/components/AdminHeader'

const initialState = {
  sport: 'basketball',
  gender: 'womens',
  level: 'high_school',
}

const reducer = (state = initialState, action) => {
  if (action.type === 'updateAdminState') {
    return { ...state, ...action.payload }
  }
  return state
}

test('displays dropdown dataset selectors on admin pages', () => {
  render(
    <Provider store={createStore(reducer)}>
      <AdminHeader />
    </Provider>,
  )

  expect(screen.getByRole('combobox', { name: 'Sport' })).toHaveValue('basketball')
  expect(screen.getByRole('combobox', { name: 'Gender' })).toHaveValue('womens')
  expect(screen.getByRole('combobox', { name: 'Level' })).toHaveValue('high_school')
  expect(screen.queryByRole('radio')).not.toBeInTheDocument()
  expect(screen.queryByRole('button', { name: 'Archive Selected Sport' })).not.toBeInTheDocument()
  expect(screen.queryByRole('button', { name: 'Archive All Sports' })).not.toBeInTheDocument()
  expect(screen.queryByRole('button', { name: 'Reset Selected Sport' })).not.toBeInTheDocument()
  expect(screen.queryByRole('button', { name: 'Reset All Sports' })).not.toBeInTheDocument()
})

test('switching to football also selects the supported mens gender', async () => {
  const user = userEvent.setup()
  const store = createStore(reducer)
  render(
    <Provider store={store}>
      <AdminHeader />
    </Provider>,
  )

  await user.selectOptions(screen.getByRole('combobox', { name: 'Sport' }), 'football')

  expect(store.getState()).toMatchObject({ sport: 'football', gender: 'mens' })
})
