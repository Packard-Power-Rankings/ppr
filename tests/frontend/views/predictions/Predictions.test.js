import React from 'react'
import { fireEvent, render, screen } from '@testing-library/react'
import Predictions from 'src/views/predictions/Predictions'

jest.mock('src/api', () => ({
  __esModule: true,
  default: { get: jest.fn() },
}))

test('uses dropdowns for sport, gender, and level and identifies Team 1 as home', () => {
  render(<Predictions />)

  const sportSelect = screen.getByRole('combobox', { name: 'Sport:' })
  const genderSelect = screen.getByRole('combobox', { name: 'Gender:' })
  const levelSelect = screen.getByRole('combobox', { name: 'Level:' })

  expect(sportSelect).toHaveValue('football')
  expect(genderSelect).toHaveValue('mens')
  expect(levelSelect).toHaveValue('high_school')

  fireEvent.change(sportSelect, { target: { value: 'basketball' } })
  fireEvent.change(genderSelect, { target: { value: 'womens' } })
  fireEvent.change(levelSelect, { target: { value: 'college' } })

  expect(sportSelect).toHaveValue('basketball')
  expect(genderSelect).toHaveValue('womens')
  expect(levelSelect).toHaveValue('college')
  const homeFieldAdvantage = screen.getByRole('checkbox', {
    name: 'Apply home-field advantage to Team 1 (home team)',
  })
  expect(homeFieldAdvantage).toBeChecked()
  fireEvent.click(homeFieldAdvantage)
  expect(homeFieldAdvantage).not.toBeChecked()
})