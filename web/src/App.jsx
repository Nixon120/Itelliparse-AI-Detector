import React from 'react';
import { Outlet, NavLink, useLocation } from 'react-router-dom';

const NavItem = ({ to, children }) => (
  <NavLink to={to} className={({isActive}) => `block px-3 py-2 rounded-lg mb-1 ${isActive ? 'bg-sky-100 text-sky-700' : 'hover:bg-slate-100'}`}>
    {children}
  </NavLink>
);

export default function App() {
  const location = useLocation();
  const showSidebar = location.pathname !== '/';
  return (
    <div>
      {showSidebar && (
        <aside className='sidebar'>
          <div className='text-xl font-bold mb-4'>intelliparse</div>
          <nav>
            <NavItem to='/dashboard'>Dashboard</NavItem>
            <NavItem to='/playground'>Playground</NavItem>
            <NavItem to='/endpoints'>Endpoints</NavItem>
            <NavItem to='/pricing'>Pricing</NavItem>
            <NavItem to='/settings'>Settings</NavItem>
          </nav>
          <div className='mt-6 text-xs text-slate-500'>v1.0.0</div>
        </aside>
      )}
      <main className={showSidebar ? 'main' : ''}>
        <Outlet />
      </main>
    </div>
  );
}
