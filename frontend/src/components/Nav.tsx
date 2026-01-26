import React from 'react';
import { Link, useLocation } from 'react-router-dom';

export default function Nav() {
  const location = useLocation();
  const isActive = (path: string) => location.pathname === path;

  return (
    <nav className="sticky top-0 z-50 px-4 py-4">
      <div className="glass-panel max-w-7xl mx-auto rounded-2xl px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-8">
          <Link
            to="/"
            className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-primary-600 to-primary-400 tracking-tight"
          >
            Arsip Kelurahan
          </Link>
          <div className="hidden md:flex items-center gap-1">
            <NavLink to="/" active={isActive('/')}>
              Dashboard
            </NavLink>
            <NavLink to="/search" active={isActive('/search')}>
              Arsip
            </NavLink>
            <NavLink to="/upload" active={isActive('/upload')}>
              Unggah
            </NavLink>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-primary-100 text-primary-600 flex items-center justify-center font-bold text-sm border border-primary-200">
            A
          </div>
        </div>
      </div>
    </nav>
  );
}

const NavLink = ({
  to,
  children,
  active,
}: {
  to: string;
  children: React.ReactNode;
  active: boolean;
}) => (
  <Link
    to={to}
    className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
      active
        ? 'bg-primary-50 text-primary-700 shadow-sm'
        : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
    }`}
  >
    {children}
  </Link>
);
