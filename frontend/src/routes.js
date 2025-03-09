import { element, exact } from 'prop-types'
import React from 'react'

const Dashboard = React.lazy(() => import('./views/dashboard/Dashboard'))
// const Colors = React.lazy(() => import('./views/theme/colors/Colors'))
// const Typography = React.lazy(() => import('./views/theme/typography/Typography'))

// Admin
const AddTeams = React.lazy(() => import('./views/admin/add_teams/AddTeams'))
const CalculateValues = React.lazy(() => import('./views/admin/calc_values/CalculateValues'))
const UpdateGame = React.lazy(() => import('./views/admin/update_game/UpdateGame'))
const UpdateTeamName = React.lazy(() => import('./views/admin/update_team_name/UpdateTeamName'))
const DeleteTeam = React.lazy(() => import('./views/admin/delete_team/DeleteTeam'))
const DeleteGame = React.lazy(() => import('./views/admin/delete_game/DeleteGame'))

// Base
// const Accordion = React.lazy(() => import('./views/base/accordion/Accordion'))
// const Breadcrumbs = React.lazy(() => import('./views/base/breadcrumbs/Breadcrumbs'))
// const Cards = React.lazy(() => import('./views/base/cards/Cards'))
// const Carousels = React.lazy(() => import('./views/base/carousels/Carousels'))
// const Collapses = React.lazy(() => import('./views/base/collapses/Collapses'))
// const ListGroups = React.lazy(() => import('./views/base/list-groups/ListGroups'))
// const Navs = React.lazy(() => import('./views/base/navs/Navs'))
// const Paginations = React.lazy(() => import('./views/base/paginations/Paginations'))
// const Placeholders = React.lazy(() => import('./views/base/placeholders/Placeholders'))
// const Popovers = React.lazy(() => import('./views/base/popovers/Popovers'))
// const Progress = React.lazy(() => import('./views/base/progress/Progress'))
// const Spinners = React.lazy(() => import('./views/base/spinners/Spinners'))
// const Tables = React.lazy(() => import('./views/base/tables/Tables'))
// const Tooltips = React.lazy(() => import('./views/base/tooltips/Tooltips'))

// Buttons
// const Buttons = React.lazy(() => import('./views/buttons/buttons/Buttons'))
// const ButtonGroups = React.lazy(() => import('./views/buttons/button-groups/ButtonGroups'))
// const Dropdowns = React.lazy(() => import('./views/buttons/dropdowns/Dropdowns'))

//Forms
// const ChecksRadios = React.lazy(() => import('./views/forms/checks-radios/ChecksRadios'))
// const FloatingLabels = React.lazy(() => import('./views/forms/floating-labels/FloatingLabels'))
// const FormControl = React.lazy(() => import('./views/forms/form-control/FormControl'))
// const InputGroup = React.lazy(() => import('./views/forms/input-group/InputGroup'))
// const Layout = React.lazy(() => import('./views/forms/layout/Layout'))
// const Range = React.lazy(() => import('./views/forms/range/Range'))
// const Select = React.lazy(() => import('./views/forms/select/Select'))
// const Validation = React.lazy(() => import('./views/forms/validation/Validation'))

// const Charts = React.lazy(() => import('./views/charts/Charts'))

// Icons
// const CoreUIIcons = React.lazy(() => import('./views/icons/coreui-icons/CoreUIIcons'))
// const Flags = React.lazy(() => import('./views/icons/flags/Flags'))
// const Brands = React.lazy(() => import('./views/icons/brands/Brands'))

// Notifications
// const Alerts = React.lazy(() => import('./views/notifications/alerts/Alerts'))
// const Badges = React.lazy(() => import('./views/notifications/badges/Badges'))
// const Modals = React.lazy(() => import('./views/notifications/modals/Modals'))
// const Toasts = React.lazy(() => import('./views/notifications/toasts/Toasts'))

// const Widgets = React.lazy(() => import('./views/widgets/Widgets'))

// Teams Info
const Teams = React.lazy(() => import('./views/teams/Teams'))

// Team Info
const Team = React.lazy(() => import('./views/team/Team'))

// Predictions
const Predictions = React.lazy(() => import('./views/predictions/Predictions'))

const routes = [
  { path: '/', exact: true, name: 'Home' },
  { path: '/dashboard', name: 'Dashboard', element: Dashboard },
  { path: '/teams/:sport/:gender/:level', name: 'Teams', element: Teams },
  { path: '/team/:team_name/:sport/:gender/:level', name: "Team", element: Team },
  { path: '/predictions', name: 'Predictions', element: Predictions },
  { path: '/admin', name: 'Admin', element: AddTeams, exact: true },
  { path: '/admin/add_teams', name: 'AddTeams', element: AddTeams },
  { path: '/admin/calc_values', name: 'CalculateValues', element: CalculateValues },
  { path: '/admin/update_game', name: 'UpdateGame', element: UpdateGame },
  { path: '/admin/update_team_name', name: 'UpdateTeamName', element: UpdateTeamName },
  { path: '/admin/delete_team', name: 'DeleteTeam', element: DeleteTeam},
  { path: '/admin/delete_game', name: 'DeleteGame', element: DeleteGame},
]

export default routes
