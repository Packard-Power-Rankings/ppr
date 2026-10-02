import React from 'react'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import Login from 'src/views/pages/login/Login'

jest.mock('react-redux', () => ({
  useSelector: (selector) => selector({ authReady: true, isAdmin: false }),
}))

jest.mock('src/services/authService', () => ({
  loginUser: jest.fn(),
}))

test('show password checkbox reveals the typed password and masks it when unchecked', async () => {
  const user = userEvent.setup()
  render(
    <MemoryRouter>
      <Login />
    </MemoryRouter>,
  )

  const passwordInput = screen.getByPlaceholderText('Password')
  const showPasswordCheckbox = screen.getByRole('checkbox', { name: 'Show password' })

  expect(passwordInput).toHaveAttribute('type', 'password')
  await user.type(passwordInput, 'secret-value')
  await user.click(showPasswordCheckbox)

  expect(passwordInput).toHaveAttribute('type', 'text')
  expect(passwordInput).toHaveValue('secret-value')
  expect(showPasswordCheckbox).toBeChecked()

  await user.click(showPasswordCheckbox)

  expect(passwordInput).toHaveAttribute('type', 'password')
  expect(passwordInput).toHaveValue('secret-value')
  expect(showPasswordCheckbox).not.toBeChecked()
})