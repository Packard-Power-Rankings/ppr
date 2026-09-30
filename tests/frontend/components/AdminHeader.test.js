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

test('only displays dataset selectors on admin pages', () => {
  render(
    <Provider store={createStore(reducer)}>
      <AdminHeader />
    </Provider>,
  )

  expect(screen.getByRole('radio', { name: 'Basketball' })).toBeChecked()
  expect(screen.getByRole('radio', { name: 'Womens' })).toBeChecked()
  expect(screen.queryByRole('button', { name: 'Archive Season' })).not.toBeInTheDocument()
  expect(screen.queryByRole('button', { name: 'Clear Season' })).not.toBeInTheDocument()
})

test('switching to football also selects the supported mens gender', async () => {
  const user = userEvent.setup()
  const store = createStore(reducer)
  render(
    <Provider store={store}>
      <AdminHeader />
    </Provider>,
  )

  await user.click(screen.getByRole('radio', { name: 'Football' }))

  expect(store.getState()).toMatchObject({ sport: 'football', gender: 'mens' })
})
