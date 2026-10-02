import React from 'react'
import CIcon from '@coreui/icons-react'
import {
  cilAmericanFootball,
  cilBasketball,
  cilInfo,
  cilFunctions,
  cilCog,
  cilHistory,
  cilSchool,
  cilBuilding,
  cilUser,
  cilUserFemale,
  cilCalendar,
  cilDescription,
  cilLockLocked,
  cilSettings
} from '@coreui/icons'
import { CNavGroup, CNavItem, CNavTitle } from '@coreui/react'

const Navigation = (isAdmin) => {
  const _nav = [
    ...(isAdmin ? [
      {
        component: CNavTitle,
        name: "Admin",
      },
      {
        component: CNavItem,
        name: 'Dashboard',
        to: '/admin',
        icon: <CIcon icon={cilCog} customClassName='nav-icon' />,
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
          to: '/football/mens/high_school',
          icon: <CIcon icon={cilSchool} customClassName="nav-icon" />,
        },
        {
          component: CNavItem,
          name: 'College',
          to: '/football/mens/college',
          icon: <CIcon icon={cilBuilding} customClassName="nav-icon" />,
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
          icon: <CIcon icon={cilUser} customClassName="nav-icon" />,
          items: [
            {
              component: CNavItem,
              name: 'High School',
              to: '/basketball/mens/high_school',
              icon: <CIcon icon={cilSchool} customClassName="nav-icon" />,
            },
            {
              component: CNavItem,
              name: 'College',
              to: '/basketball/mens/college',
              icon: <CIcon icon={cilBuilding} customClassName="nav-icon" />,
            }
          ]
        },
        {
          component: CNavGroup,
          name: 'Womens',
          to: '#',
          icon: <CIcon icon={cilUserFemale} customClassName="nav-icon" />,
          items: [
            {
              component: CNavItem,
              name: 'High School',
              to: '/basketball/womens/high_school',
              icon: <CIcon icon={cilSchool} customClassName="nav-icon" />,
            },
            {
              component: CNavItem,
              name: 'College',
              to: '/basketball/womens/college',
              icon: <CIcon icon={cilBuilding} customClassName="nav-icon" />,
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
          icon: <CIcon icon={cilCalendar} customClassName="nav-icon" />,
        },
      ],
    },
    {
      component: CNavItem,
      name: 'Prediction',
      to: '/prediction',
      icon: <CIcon icon={cilFunctions} customClassName="nav-icon" />
    },
    {
      component: CNavGroup,
      name: 'SITE INFO',
      icon: <CIcon icon={cilInfo} customClassName="nav-icon" />,
      items: [
        {
          component: CNavItem,
          name: 'About',
          to: '/about',
          icon: <CIcon icon={cilInfo} customClassName="nav-icon" />,
        },
        {
          component: CNavItem,
          name: 'Terms Of Service',
          to: '/tos',
          icon: <CIcon icon={cilDescription} customClassName="nav-icon" />,
        },
        {
          component: CNavItem,
          name: 'Privacy Policy',
          to: '/privacy',
          icon: <CIcon icon={cilLockLocked} customClassName="nav-icon" />,
        },
        {
          component: CNavItem,
          name: 'Cookies Policy',
          to: '/cookies',
          icon: <CIcon icon={cilSettings} customClassName="nav-icon" />,
        }
      ]
    },
  ]

  return _nav
}

export default Navigation
