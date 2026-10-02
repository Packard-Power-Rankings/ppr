import React from 'react'
import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import navigation from 'src/_nav'
import routes from 'src/routes'
import { cilInfo } from '@coreui/icons'

test('uses the Dashboard item as the admin entry point', () => {
  const dashboardItem = navigation(true).find((item) => item.name === 'Dashboard')

  expect(dashboardItem).toBeDefined()
  expect(dashboardItem.to).toBe('/admin')
})

test('maps the protected admin root to the dashboard route', () => {
  const adminRoute = routes.find((route) => route.path === '/admin')

  expect(adminRoute).toMatchObject({ name: 'Admin Dashboard', admin: true })
  expect(adminRoute.element).toBeDefined()
})

test('uses Add Games and Add Teams as separate admin ingestion routes', () => {
  expect(routes.find((route) => route.path === '/admin/add_games')).toMatchObject({
    name: 'Add Games',
    admin: true,
  })
  expect(routes.find((route) => route.path === '/admin/add_teams')).toMatchObject({
    name: 'Add Teams',
    admin: true,
  })
})

test('separates the protected Ranking and Z-Score admin routes', () => {
  const rankingRoute = routes.find((route) => route.path === '/admin/ranking')
  const zScoreRoute = routes.find((route) => route.path === '/admin/z_scores')

  expect(rankingRoute).toMatchObject({ admin: true })
  expect(rankingRoute.name).toMatch(/ Ranking$/)
  expect(zScoreRoute).toMatchObject({ name: 'Z-Score', admin: true })
  expect(zScoreRoute.element).toBeDefined()
})

test('places the Site Info accordion after Prediction with its info icon', () => {
  const items = navigation(false)
  const predictionsIndex = items.findIndex((item) => item.name === 'Prediction')
  const siteInfoIndex = items.findIndex((item) => item.name.toLowerCase() === 'site info')
  const siteInfo = items[siteInfoIndex]

  expect(predictionsIndex).toBeGreaterThan(-1)
  expect(items[predictionsIndex].to).toBe('/prediction')
  expect(siteInfoIndex).toBeGreaterThan(predictionsIndex)
  expect(siteInfo.icon.props.icon).toEqual(cilInfo)
  expect(siteInfo.items).toEqual([
    expect.objectContaining({ name: 'About', to: '/about' }),
    expect.objectContaining({ name: 'Terms Of Service', to: '/tos' }),
    expect.objectContaining({ name: 'Privacy Policy', to: '/privacy' }),
    expect.objectContaining({ name: 'Cookies Policy', to: '/cookies' }),
  ])
  expect(items.some((item) => item.name === 'Info' && item.items)).toBe(false)
})

test('redirects the old prediction route to the singular route', async () => {
  const legacyRoute = routes.find((route) => route.path === '/predictions')
  const LegacyRedirect = legacyRoute.element

  expect(routes.find((route) => route.path === '/prediction')).toMatchObject({
    name: 'Prediction',
  })

  render(
    <MemoryRouter initialEntries={['/predictions']}>
      <Routes>
        <Route path="/predictions" element={<LegacyRedirect />} />
        <Route path="/prediction" element={<div>Prediction page</div>} />
      </Routes>
    </MemoryRouter>,
  )

  expect(await screen.findByText('Prediction page')).toBeInTheDocument()
})

test('redirects the retired unfiltered teams page to home', async () => {
  const legacyRoute = routes.find((route) => route.path === '/teams')
  const LegacyRedirect = legacyRoute.element

  render(
    <MemoryRouter initialEntries={['/teams']}>
      <Routes>
        <Route path="/teams" element={<LegacyRedirect />} />
        <Route path="/" element={<div>Home page</div>} />
      </Routes>
    </MemoryRouter>,
  )

  expect(await screen.findByText('Home page')).toBeInTheDocument()
})

test('uses sport-first URLs for ranking navigation', () => {
  const items = navigation(false)
  const football = items.find((item) => item.name === 'Football')
  const basketball = items.find((item) => item.name === 'Basketball')

  expect(football.items).toEqual([
    expect.objectContaining({ name: 'High School', to: '/football/mens/high_school' }),
    expect.objectContaining({ name: 'College', to: '/football/mens/college' }),
  ])
  expect(basketball.items[0].items).toEqual([
    expect.objectContaining({ name: 'High School', to: '/basketball/mens/high_school' }),
    expect.objectContaining({ name: 'College', to: '/basketball/mens/college' }),
  ])
})

test('redirects legacy team ranking URLs to sport-first URLs', async () => {
  const legacyRoute = routes.find(
    (route) => route.path === '/teams/:sport/:gender/:level',
  )
  const LegacyRedirect = legacyRoute.element

  render(
    <MemoryRouter initialEntries={['/teams/basketball/mens/college']}>
      <Routes>
        <Route path={legacyRoute.path} element={<LegacyRedirect />} />
        <Route path="/basketball/mens/college" element={<div>College Rankings</div>} />
      </Routes>
    </MemoryRouter>,
  )

  expect(await screen.findByText('College Rankings')).toBeInTheDocument()
})

test('keeps legacy Site Info URLs as redirects', () => {
  expect(routes.find((route) => route.path === '/about')?.element).toBeDefined()
  expect(routes.find((route) => route.path === '/tos')?.element).toBeDefined()
  expect(routes.find((route) => route.path === '/privacy')?.element).toBeDefined()
  expect(routes.find((route) => route.path === '/cookies')?.element).toBeDefined()

  expect(routes.find((route) => route.path === '/info/about')?.element).toBeDefined()
  expect(routes.find((route) => route.path === '/info/tos')?.element).toBeDefined()
  expect(routes.find((route) => route.path === '/info/privacy')?.element).toBeDefined()
  expect(routes.find((route) => route.path === '/info/cookies')?.element).toBeDefined()
})
