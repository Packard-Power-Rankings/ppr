import React from 'react'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import AppBreadcrumb from 'src/components/AppBreadcrumb'

test('shows sport, gender, and level breadcrumbs for basketball', () => {
  render(
    <MemoryRouter initialEntries={['/teams/basketball/mens/high_school']}>
      <AppBreadcrumb />
    </MemoryRouter>,
  )

  expect(screen.getByRole('link', { name: 'Basketball' })).toHaveAttribute(
    'href',
    '/teams/basketball',
  )
  expect(screen.getByRole('link', { name: 'Mens' })).toHaveAttribute(
    'href',
    '/teams/basketball/mens',
  )
  expect(screen.getByText('High School')).toHaveAttribute('aria-current', 'page')
})

test('omits the gender breadcrumb when the sport has no gender choice', () => {
  render(
    <MemoryRouter initialEntries={['/teams/football/mens/college']}>
      <AppBreadcrumb />
    </MemoryRouter>,
  )

  expect(screen.getByRole('link', { name: 'Football' })).toHaveAttribute(
    'href',
    '/teams/football',
  )
  expect(screen.queryByText('Mens')).not.toBeInTheDocument()
  expect(screen.getByText('College')).toHaveAttribute('aria-current', 'page')
})
