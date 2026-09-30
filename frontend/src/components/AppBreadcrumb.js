import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { CBreadcrumb, CBreadcrumbItem } from '@coreui/react';
import { formatDisplayName } from 'src/utils/displayNames';

const SPORTS_WITH_GENDER_BREADCRUMBS = new Set(['basketball']);

const AppBreadcrumb = () => {
  const currentLocation = useLocation().pathname;

  const formatRouteName = (name) => {
    try {
      return formatDisplayName(decodeURIComponent(name));
    } catch {
      return formatDisplayName(name);
    }
  };

  const getBreadcrumbs = (location) => {
    const pathSegments = location.split('/').filter(segment => segment);

    if (pathSegments[0] === 'teams') {
      if (pathSegments.length === 1) {
        return [{ pathname: '/teams', name: 'Teams', active: true }];
      }

      const [, sport, gender, level] = pathSegments;
      const showGender = SPORTS_WITH_GENDER_BREADCRUMBS.has(sport);
      const breadcrumbs = [
        {
          pathname: `/teams/${sport}`,
          name: formatDisplayName(sport),
          active: !level && (!showGender || !gender),
        },
      ];

      if (showGender && gender) {
        breadcrumbs.push({
          pathname: `/teams/${sport}/${gender}`,
          name: formatDisplayName(gender),
          active: !level,
        });
      }

      if (level) {
        breadcrumbs.push({
          pathname: location,
          name: formatDisplayName(level),
          active: true,
        });
      }

      return breadcrumbs;
    }

    if (pathSegments[0] === 'team' && pathSegments.length >= 5) {
      const [, teamName, sport, gender, level] = pathSegments;
      const showGender = SPORTS_WITH_GENDER_BREADCRUMBS.has(sport);
      const breadcrumbs = [
        {
          pathname: `/teams/${sport}`,
          name: formatDisplayName(sport),
          active: false,
        },
      ];

      if (showGender) {
        breadcrumbs.push({
          pathname: `/teams/${sport}/${gender}`,
          name: formatDisplayName(gender),
          active: false,
        });
      }

      breadcrumbs.push(
        {
          pathname: `/teams/${sport}/${gender}/${level}`,
          name: formatDisplayName(level),
          active: false,
        },
        { pathname: location, name: formatRouteName(teamName), active: true },
      );

      return breadcrumbs;
    }

    let currentPath = '';
    return pathSegments.map((segment, index) => {
      currentPath += `/${segment}`;
      return {
        pathname: currentPath,
        name: formatRouteName(segment),
        active: index === pathSegments.length - 1,
      };
    });
  };

  const breadcrumbs = getBreadcrumbs(currentLocation);

  return (
    <CBreadcrumb className="my-0">
      <CBreadcrumbItem>
        <Link to="/">Home</Link>
      </CBreadcrumbItem>
      {breadcrumbs.map((breadcrumb) =>
        breadcrumb.active ? (
          <CBreadcrumbItem active key={breadcrumb.pathname}>
            {breadcrumb.name}
          </CBreadcrumbItem>
        ) : (
          <CBreadcrumbItem key={breadcrumb.pathname}>
            <Link to={breadcrumb.pathname}>{breadcrumb.name}</Link>
          </CBreadcrumbItem>
        ),
      )}
    </CBreadcrumb>
  );
};

export default React.memo(AppBreadcrumb);
