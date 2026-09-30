import React from 'react'
import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import api from 'src/api'
import Teams from 'src/views/teams/Teams'

jest.mock('src/api', () => ({
  __esModule: true,
  default: {
    get: jest.fn(),
  },
}))

const renderTeams = () =>
  render(
    <MemoryRouter initialEntries={['/teams/basketball/mens/high_school']}>
      <Routes>
        <Route path="/teams/:sport/:gender/:level" element={<Teams />} />
      </Routes>
    </MemoryRouter>,
  )

beforeEach(() => {
  api.get.mockReset()
})

test('shows a blue message when the selected database has no teams', async () => {
  api.get.mockResolvedValue({
    data: {
      status: 204,
      data: null,
    },
  })

  renderTeams()

  const message = await screen.findByText(
    'No Data Found in Database for High School Mens Basketball',
  )
  expect(message).toHaveClass('text-primary')
})

test('shows a red message when teams data cannot be loaded', async () => {
  const consoleError = jest.spyOn(console, 'error').mockImplementation(() => {})
  api.get.mockRejectedValue(new Error('Network unavailable'))

  renderTeams()

  const message = await screen.findByText('Failed to Load High School Mens Basketball Data')
  expect(message).toHaveClass('text-danger')
  consoleError.mockRestore()
})
