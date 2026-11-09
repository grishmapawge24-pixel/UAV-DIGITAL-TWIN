import React from 'react';
import { NavLink } from 'react-router-dom';

const links = [
  { to: '/', label: 'DASHBOARD', end: true },
  { to: '/map-simulation', label: 'MAP SIMULATION' },
  { to: '/simulation', label: 'ENGINE SIMULATION' },
  { to: '/replay', label: 'MISSION REPLAY' },
  { to: '/diagnostics', label: 'DIAGNOSTICS' }
];

export default function RouteNav() {
  return (
    <nav className="route-nav">
      {links.map((l) => (
        <NavLink
          key={l.to}
          to={l.to}
          end={l.end}
          className={({ isActive }) => `route-nav-item${isActive ? ' active' : ''}`}
        >
          {l.label}
        </NavLink>
      ))}
    </nav>
  );
}
