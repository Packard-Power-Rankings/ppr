import navigation from 'src/_nav'
import routes from 'src/routes'

test('uses the Admin accordion as a single dashboard entry point', () => {
  const adminGroup = navigation(true).find((item) => item.name === 'Admin' && item.items)

  expect(adminGroup).toBeDefined()
  expect(adminGroup.to).toBe('/admin')
  expect(adminGroup.items).toEqual([
    expect.objectContaining({ name: 'Dashboard', to: '/admin' }),
  ])
})

test('maps the protected admin root to the dashboard route', () => {
  const adminRoute = routes.find((route) => route.path === '/admin')

  expect(adminRoute).toMatchObject({ name: 'Admin Dashboard', admin: true })
  expect(adminRoute.element).toBeDefined()
})
