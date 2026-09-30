import React from 'react'
import CIcon from '@coreui/icons-react'
import {
  cilAmericanFootball,
  cilBasketball,
  cilInfo,
  cilFunctions,
  cilCog,
  cilHistory
} from '@coreui/icons'
import { CNavGroup, CNavItem, CNavTitle } from '@coreui/react'

const Navigation = (isAdmin) => {
  const _nav = [
    {
      component: CNavTitle,
      name: 'Site Info'
    },
    {
      component: CNavGroup,
      name: 'Info',
      to: '/info',
      icon: <CIcon icon={cilInfo} customClassName="nav-icon" />,
      items: [
        {
          component: CNavItem,
          name: 'About',
          to: '/info/about'
        },
        {
          component: CNavItem,
          name: 'Terms Of Service',
          to: '/info/tos'
        },
        {
          component: CNavItem,
          name: 'Privacy Policy',
          to: '/info/privacy'
        },
        {
          component: CNavItem,
          name: 'Cookies Policy',
          to: '/info/cookies'
        }
      ]
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
            name: 'Dashboard',
            to: '/admin',
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
      component: CNavGroup,
      name: 'Archive',
      to: '#',
      icon: <CIcon icon={cilHistory} customClassName="nav-icon" />,
      items: [
        {
          component: CNavItem,
          name: 'All Seasons',
          to: '/archives',
        },
      ],
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
