import React from 'react';
import { Outlet, NavLink, useLocation, Link } from 'react-router-dom';

const NavItem = ({ to, children }) => (
  <NavLink to={to} className={({isActive}) => `block px-3 py-2 rounded-lg mb-1 ${isActive ? 'bg-sky-100 text-sky-700' : 'hover:bg-slate-100'}`}>
    {children}
  </NavLink>
);

function Topbar(){
  const user = JSON.parse(localStorage.getItem('ip_user') || 'null');
  return (
    <div className="w-full border-b border-slate-200 bg-white">
      <div className="container flex items-center justify-between py-3">
        <Link to="/" className="font-bold">intelliparse</Link>
        <div className="flex gap-3 items-center">
          {!user && <Link className="link" to="/login">Sign in</Link>}
          {!user && <Link className="btn" to="/register">Sign up</Link>}
          {user && <span className="text-slate-600 text-sm">{user.email}</span>}
          {user && <Link className="btn" to="/dashboard">Open app</Link>}
        </div>
      </div>
    </div>
  );
}

export default function App() {
  const location = useLocation();
  const showSidebar = !['/', '/login', '/register'].includes(location.pathname);

  return (
    <div>
      <Topbar />
      {showSidebar && (
        <aside className='sidebar'>
          <div className='text-xl font-bold mb-4'>App</div>
          <nav>
            <NavItem to='/dashboard'>Dashboard</NavItem>
            <NavItem to='/playground'>Playground</NavItem>
            <NavItem to='/endpoints'>Endpoints</NavItem>
            <NavItem to='/pricing'>Pricing</NavItem>
            <NavItem to='/settings'>Settings</NavItem>
          </nav>
          <div className='mt-6 text-xs text-slate-500'>v1.1.0</div>
        </aside>
      )}
      <main className={showSidebar ? 'main' : ''}>
        <Outlet />
      </main>
    </div>
  );
}
