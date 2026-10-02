import React from 'react'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import AppBreadcrumb from 'src/components/AppBreadcrumb'

test('shows sport, gender, and level breadcrumbs for basketball', () => {
  render(
    <MemoryRouter initialEntries={['/basketball/mens/high_school']}>
      <AppBreadcrumb />
    </MemoryRouter>,
  )

  expect(screen.getByRole('link', { name: 'Basketball' })).toHaveAttribute(
    'href',
    '/basketball',
  )
  expect(screen.getByRole('link', { name: 'Mens' })).toHaveAttribute(
    'href',
    '/basketball/mens',
  )
  expect(screen.getByText('High School')).toHaveAttribute('aria-current', 'page')
})

test('omits the gender breadcrumb when the sport has no gender choice', () => {
  render(
    <MemoryRouter initialEntries={['/football/mens/college']}>
      <AppBreadcrumb />
    </MemoryRouter>,
  )

  expect(screen.getByRole('link', { name: 'Football' })).toHaveAttribute(
    'href',
    '/football',
  )
  expect(screen.queryByText('Mens')).not.toBeInTheDocument()
  expect(screen.getByText('College')).toHaveAttribute('aria-current', 'page')
})

test('links team detail breadcrumbs back to sport-first ranking pages', () => {
  render(
    <MemoryRouter initialEntries={['/team/Northstar%20Academy/basketball/womens/college']}>
      <AppBreadcrumb />
    </MemoryRouter>,
  )

  expect(screen.getByRole('link', { name: 'Basketball' })).toHaveAttribute(
    'href',
    '/basketball',
  )
  expect(screen.getByRole('link', { name: 'Womens' })).toHaveAttribute(
    'href',
    '/basketball/womens',
  )
  expect(screen.getByRole('link', { name: 'College' })).toHaveAttribute(
    'href',
    '/basketball/womens/college',
  )
  expect(screen.getByText('Northstar Academy')).toHaveAttribute('aria-current', 'page')
})

test('shows the singular Prediction breadcrumb', () => {
  render(
    <MemoryRouter initialEntries={['/prediction']}>
      <AppBreadcrumb />
    </MemoryRouter>,
  )

  expect(screen.getByText('Prediction')).toHaveAttribute('aria-current', 'page')
})
