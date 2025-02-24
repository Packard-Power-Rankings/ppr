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

const Navigation = (isAdmin) => {
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
    ...(isAdmin ? [
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
    ]: []),
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

  return _nav
}

export default Navigation
