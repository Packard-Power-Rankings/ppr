import React from 'react';
import { useLocation } from 'react-router-dom';
import { CBreadcrumb, CBreadcrumbItem } from '@coreui/react';

const AppBreadcrumb = () => {
  const currentLocation = useLocation().pathname;

  // Helper function to capitalize and format route names
  const formatRouteName = (name) => {
    return name
      .split(/(?:_|%20)+/)
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  const getBreadcrumbs = (location) => {
    const excludeArr = ["football", "basketball", "mens", "womens", "high_school", "college"];
    const breadcrumbs = [];
    const pathSegments = location.split('/').filter(segment => segment);
    let currentPath = '';

    // pathSegments.forEach((segment, index) => {
    //   if (index !== 1)
    //     currentPath += `/${segment}`;
    // });

    const removedSegments = pathSegments.filter(removed => !excludeArr.some(t => removed.includes(t)))

    // let currentPath = '';
    removedSegments.forEach((segment, index) => {
      currentPath += `/${segment}`;

      breadcrumbs.push({
        pathname: currentPath,
        name: formatRouteName(segment),
        active: index === pathSegments.length - 1
      });
    });

    return breadcrumbs;
  };

  const breadcrumbs = getBreadcrumbs(currentLocation);

  return (
    <CBreadcrumb className="my-0">
      <CBreadcrumbItem href="/">Home</CBreadcrumbItem>
      {breadcrumbs.map((breadcrumb) => (
        <CBreadcrumbItem
          {...(breadcrumb.active ? { active: true } : { href: breadcrumb.pathname })}
          key={breadcrumb.pathname}
        >
          {breadcrumb.name}
        </CBreadcrumbItem>
      ))}
    </CBreadcrumb>
  );
};

export default React.memo(AppBreadcrumb);