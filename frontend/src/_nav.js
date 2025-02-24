import React from 'react'
import CIcon from '@coreui/icons-react'
import {
  cilAmericanFootball,
  cilBasketball,
  cilInfo,
  cilFunctions,
  cilCog
} from '@coreui/icons'
import { CNavGroup, CNavItem, CNavTitle } from '@coreui/react'

const _nav = [
  {
    component: CNavTitle,
    name: 'About'
  },
  {
    component: CNavItem,
    name: 'Info',
    to: '/about',
    icon: <CIcon icon={cilInfo} customClassName="nav-icon" />
  },
  {
    component: CNavTitle,
    name: "Admin"
  },
  {
    component: CNavGroup,
    name: 'Admin',
    to: '/admin',
    icon: <CIcon icon={cilCog} customClassName='nav-icon' />,
    items: [
      {
        component: CNavItem,
        name: 'Add Teams',
        to: '/admin/add_teams',
      },
      {
        component: CNavItem,
        name: 'Algorithm/z-scores',
        to: '/admin/calc_values',
      },
      {
        component: CNavItem,
        name: 'Clear Season',
        to: '/admin/clear_season',
      },
      {
        component: CNavItem,
        name: 'Delete Game',
        to: '/admin/delete_game',
      },
      {
        component: CNavItem,
        name: 'Delete Team',
        to: '/admin/delete_team',
      },
      {
        component: CNavItem,
        name: 'Update Game',
        to: '/admin/update_game',
      },
      {
        component: CNavItem,
        name: 'Update Team Name',
        to: '/admin/update_team_name',
      },
    ]
  },
  {
    component: CNavTitle,
    name: 'Sports'
  },
  {
    component: CNavGroup,
    name: 'Football',
    to: '#',
    icon: <CIcon icon={cilAmericanFootball} customClassName="nav-icon" />,
    items: [
      {
        component: CNavItem,
        name: 'High School',
        to: '/teams/football/mens/high_school',
      },
      {
        component: CNavItem,
        name: 'College',
        to: '/teams/football/mens/college'
      }
    ]
  },
  {
    component: CNavGroup,
    name: 'Basketball',
    to: '#',
    icon: <CIcon icon={cilBasketball} customClassName="nav-icon" />,
    items: [
      {
        component: CNavGroup,
        name: 'Mens',
        to: '#',
        items: [
          {
            component: CNavItem,
            name: 'High School',
            to: '/teams/basketball/mens/high_school',
          },
          {
            component: CNavItem,
            name: 'College',
            to: '/teams/basketball/mens/college',
          }
        ]
      },
      {
        component: CNavGroup,
        name: 'Womens',
        to: '#',
        items: [
          {
            component: CNavItem,
            name: 'High School',
            to: '/teams/basketball/womens/high_school',
          },
          {
            component: CNavItem,
            name: 'College',
            to: '/teams/basketball/womens/college'
          }
        ]
      }
    ]
  },
  {
    component: CNavTitle,
    name: 'Predictions'
  },
  {
    component: CNavItem,
    name: 'Win Predictions',
    to: '/predictions',
    icon: <CIcon icon={cilFunctions} customClassName="nav-icon" />
  },
]

// const _nav = [
//   {
//     component: CNavItem,
//     name: 'Dashboard',
//     to: '/dashboard',
//     icon: <CIcon icon={cilSpeedometer} customClassName="nav-icon" />,
//     badge: {
//       color: 'info',
//       text: 'NEW',
//     },
//   },
//   {
//     component: CNavTitle,
//     name: 'Theme',
//   },
//   {
//     component: CNavItem,
//     name: 'Colors',
//     to: '/theme/colors',
//     icon: <CIcon icon={cilDrop} customClassName="nav-icon" />,
//   },
//   {
//     component: CNavItem,
//     name: 'Typography',
//     to: '/theme/typography',
//     icon: <CIcon icon={cilPencil} customClassName="nav-icon" />,
//   },
//   {
//     component: CNavTitle,
//     name: 'Components',
//   },
//   {
//     component: CNavGroup,
//     name: 'Base',
//     to: '/base',
//     icon: <CIcon icon={cilPuzzle} customClassName="nav-icon" />,
//     items: [
//       {
//         component: CNavItem,
//         name: 'Accordion',
//         to: '/base/accordion',
//       },
//       {
//         component: CNavItem,
//         name: 'Breadcrumb',
//         to: '/base/breadcrumbs',
//       },
//       {
//         component: CNavItem,
//         name: 'Cards',
//         to: '/base/cards',
//       },
//       {
//         component: CNavItem,
//         name: 'Carousel',
//         to: '/base/carousels',
//       },
//       {
//         component: CNavItem,
//         name: 'Collapse',
//         to: '/base/collapses',
//       },
//       {
//         component: CNavItem,
//         name: 'List group',
//         to: '/base/list-groups',
//       },
//       {
//         component: CNavItem,
//         name: 'Navs & Tabs',
//         to: '/base/navs',
//       },
//       {
//         component: CNavItem,
//         name: 'Pagination',
//         to: '/base/paginations',
//       },
//       {
//         component: CNavItem,
//         name: 'Placeholders',
//         to: '/base/placeholders',
//       },
//       {
//         component: CNavItem,
//         name: 'Popovers',
//         to: '/base/popovers',
//       },
//       {
//         component: CNavItem,
//         name: 'Progress',
//         to: '/base/progress',
//       },
//       {
//         component: CNavItem,
//         name: 'Spinners',
//         to: '/base/spinners',
//       },
//       {
//         component: CNavItem,
//         name: 'Tables',
//         to: '/base/tables',
//       },
//       {
//         component: CNavItem,
//         name: 'Tooltips',
//         to: '/base/tooltips',
//       },
//     ],
//   },
//   {
//     component: CNavGroup,
//     name: 'Buttons',
//     to: '/buttons',
//     icon: <CIcon icon={cilCursor} customClassName="nav-icon" />,
//     items: [
//       {
//         component: CNavItem,
//         name: 'Buttons',
//         to: '/buttons/buttons',
//       },
//       {
//         component: CNavItem,
//         name: 'Buttons groups',
//         to: '/buttons/button-groups',
//       },
//       {
//         component: CNavItem,
//         name: 'Dropdowns',
//         to: '/buttons/dropdowns',
//       },
//     ],
//   },
//   {
//     component: CNavGroup,
//     name: 'Forms',
//     icon: <CIcon icon={cilNotes} customClassName="nav-icon" />,
//     items: [
//       {
//         component: CNavItem,
//         name: 'Form Control',
//         to: '/forms/form-control',
//       },
//       {
//         component: CNavItem,
//         name: 'Select',
//         to: '/forms/select',
//       },
//       {
//         component: CNavItem,
//         name: 'Checks & Radios',
//         to: '/forms/checks-radios',
//       },
//       {
//         component: CNavItem,
//         name: 'Range',
//         to: '/forms/range',
//       },
//       {
//         component: CNavItem,
//         name: 'Input Group',
//         to: '/forms/input-group',
//       },
//       {
//         component: CNavItem,
//         name: 'Floating Labels',
//         to: '/forms/floating-labels',
//       },
//       {
//         component: CNavItem,
//         name: 'Layout',
//         to: '/forms/layout',
//       },
//       {
//         component: CNavItem,
//         name: 'Validation',
//         to: '/forms/validation',
//       },
//     ],
//   },
//   {
//     component: CNavItem,
//     name: 'Charts',
//     to: '/charts',
//     icon: <CIcon icon={cilChartPie} customClassName="nav-icon" />,
//   },
//   {
//     component: CNavGroup,
//     name: 'Icons',
//     icon: <CIcon icon={cilStar} customClassName="nav-icon" />,
//     items: [
//       {
//         component: CNavItem,
//         name: 'CoreUI Free',
//         to: '/icons/coreui-icons',
//         badge: {
//           color: 'success',
//           text: 'NEW',
//         },
//       },
//       {
//         component: CNavItem,
//         name: 'CoreUI Flags',
//         to: '/icons/flags',
//       },
//       {
//         component: CNavItem,
//         name: 'CoreUI Brands',
//         to: '/icons/brands',
//       },
//     ],
//   },
//   {
//     component: CNavGroup,
//     name: 'Notifications',
//     icon: <CIcon icon={cilBell} customClassName="nav-icon" />,
//     items: [
//       {
//         component: CNavItem,
//         name: 'Alerts',
//         to: '/notifications/alerts',
//       },
//       {
//         component: CNavItem,
//         name: 'Badges',
//         to: '/notifications/badges',
//       },
//       {
//         component: CNavItem,
//         name: 'Modal',
//         to: '/notifications/modals',
//       },
//       {
//         component: CNavItem,
//         name: 'Toasts',
//         to: '/notifications/toasts',
//       },
//     ],
//   },
//   {
//     component: CNavItem,
//     name: 'Widgets',
//     to: '/widgets',
//     icon: <CIcon icon={cilCalculator} customClassName="nav-icon" />,
//     badge: {
//       color: 'info',
//       text: 'NEW',
//     },
//   },
//   {
//     component: CNavTitle,
//     name: 'Extras',
//   },
//   {
//     component: CNavGroup,
//     name: 'Pages',
//     icon: <CIcon icon={cilStar} customClassName="nav-icon" />,
//     items: [
//       {
//         component: CNavItem,
//         name: 'Login',
//         to: '/login',
//       },
//       {
//         component: CNavItem,
//         name: 'Register',
//         to: '/register',
//       },
//       {
//         component: CNavItem,
//         name: 'Error 404',
//         to: '/404',
//       },
//       {
//         component: CNavItem,
//         name: 'Error 500',
//         to: '/500',
//       },
//     ],
//   },
//   {
//     component: CNavItem,
//     name: 'Docs',
//     href: 'https://coreui.io/react/docs/templates/installation/',
//     icon: <CIcon icon={cilDescription} customClassName="nav-icon" />,
//   },
// ]

export default _nav
