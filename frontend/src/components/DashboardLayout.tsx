import React from 'react';
import { NavLink, Outlet, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  FileText,
  Search,
  Upload,
  Bell,
  User as UserIcon,
  Menu,
  LogOut,
  BookOpen,
} from 'lucide-react';
import clsx from 'clsx';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useNotification } from '../contexts/NotificationContext';

export default function DashboardLayout() {
  const [sidebarOpen, setSidebarOpen] = React.useState(false);
  const location = useLocation();
  const { user, logout } = useAuth();
  const { notifications, unreadCount, markAllAsRead } = useNotification();
  const [showNotif, setShowNotif] = React.useState(false);

  // Close sidebar on route change (mobile)
  React.useEffect(() => {
    setSidebarOpen(false);
    setShowNotif(false);
  }, [location.pathname]);

  return (
    <div className="min-h-screen bg-slate-50 flex font-sans text-slate-900">
      {/* Mobile Sidebar Overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-slate-900/50 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar Navigation */}
      <aside
        className={clsx(
          'fixed top-0 left-0 z-50 h-full w-64 bg-white border-r border-slate-200 shadow-xl lg:shadow-none transform transition-transform duration-300 lg:translate-x-0 lg:static flex flex-col',
          sidebarOpen ? 'translate-x-0' : '-translate-x-full',
        )}
      >
        <div className="h-20 flex items-center px-4 border-b border-slate-100 shrink-0 bg-gradient-to-r from-blue-50 to-white">
          <Link to="/" className="flex items-center gap-3 w-full">
            <img
              src="/logo-jakarta.png"
              alt="Logo DKI Jakarta"
              className="w-12 h-12 object-contain"
            />
            <div className="flex flex-col">
              <span className="text-sm font-bold text-slate-800 leading-tight">Arsip Digital</span>
              <span className="text-xs text-slate-600 font-semibold">Kelurahan Pela Mampang</span>
            </div>
          </Link>
        </div>

        <div className="p-4 space-y-1 overflow-y-auto flex-1">
          <p className="px-3 text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 mt-4">
            Menu Utama
          </p>
          <NavItem to="/" icon={<LayoutDashboard size={20} />}>
            Dashboard
          </NavItem>
          <NavItem to="/upload" icon={<Upload size={20} />}>
            Unggah Dokumen
          </NavItem>
          <NavItem to="/search" icon={<BookOpen size={20} />}>
            Arsip Dokumen
          </NavItem>

          {/* Admin Only Menus */}
          {user?.role === 'admin' && (
            <>
              <p className="px-3 text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 mt-6">
                Admin
              </p>
              <NavItem to="/admin/users" icon={<UserIcon size={20} />}>
                Kelola Pengguna
              </NavItem>
            </>
          )}
        </div>

        <div className="p-4 border-t border-slate-100 bg-slate-50/50">
          <div className="flex items-center gap-3 px-2 mb-4">
            <div className="w-10 h-10 rounded-full bg-slate-200 flex items-center justify-center text-slate-600 font-bold shrink-0">
              {user?.username?.charAt(0).toUpperCase() || 'U'}
            </div>
            <div className="min-w-0">
              <p className="text-sm font-semibold text-slate-900 truncate">
                {user?.username || 'Tamu'}
              </p>
              <p className="text-xs text-slate-500 capitalize">{user?.role || 'Pengunjung'}</p>
            </div>
          </div>
          <button
            onClick={logout}
            className="w-full flex items-center gap-2 px-3 py-2 text-sm font-medium text-red-600 hover:bg-red-50 rounded-lg transition-colors"
          >
            <LogOut size={18} />
            Keluar
          </button>
        </div>
      </aside>

      {/* Main Content Areas */}
      <div className="flex-1 flex flex-col min-w-0 min-h-screen">
        {/* Top Header */}
        <header className="h-16 bg-white border-b border-slate-200 flex items-center justify-between px-4 lg:px-8 sticky top-0 z-30">
          <button
            className="p-2 -ml-2 rounded-lg text-slate-600 hover:bg-slate-100 lg:hidden"
            onClick={() => setSidebarOpen(true)}
          >
            <Menu size={24} />
          </button>

          <div className="flex-1 max-w-xl mx-4 hidden md:block">
            {/* Placeholder for global search if needed */}
          </div>

          <div className="flex items-center gap-4 relative">
            <button
              onClick={() => {
                setShowNotif(!showNotif);
                if (!showNotif && unreadCount > 0) markAllAsRead();
              }}
              className="relative p-2 rounded-full text-slate-500 hover:bg-slate-50 hover:text-primary-600 transition-colors"
              title={unreadCount > 0 ? `${unreadCount} Notifikasi baru` : 'Notifikasi'}
            >
              <Bell size={20} />
              {unreadCount > 0 && (
                <span className="absolute top-1.5 right-1.5 w-2.5 h-2.5 bg-red-500 rounded-full border-2 border-white animate-pulse"></span>
              )}
            </button>

            {/* Notification Dropdown */}
            {showNotif && (
              <>
                <div className="fixed inset-0 z-40" onClick={() => setShowNotif(false)} />
                <div className="absolute top-full right-0 mt-2 w-80 bg-white rounded-xl shadow-xl border border-slate-100 z-50 overflow-hidden animate-fade-in">
                  <div className="p-3 border-b border-slate-50 bg-slate-50/50 flex justify-between items-center">
                    <h3 className="text-sm font-semibold text-slate-700">Notifications</h3>
                  </div>
                  <div className="max-h-[300px] overflow-y-auto">
                    {notifications.length === 0 ? (
                      <div className="p-8 text-center">
                        <div className="w-10 h-10 bg-slate-50 rounded-full flex items-center justify-center mx-auto mb-2 text-slate-400">
                          <Bell size={20} />
                        </div>
                        <p className="text-sm text-slate-500">Belum ada notifikasi baru</p>
                      </div>
                    ) : (
                      <div className="divide-y divide-slate-50">
                        {notifications.map((n) => (
                          <div
                            key={n.id}
                            className={`p-4 hover:bg-slate-50 transition-colors ${!n.read ? 'bg-blue-50/30' : ''}`}
                          >
                            <p className="text-sm text-slate-700 leading-snug">{n.message}</p>
                            <p className="text-xs text-slate-400 mt-1.5">
                              {new Date(n.timestamp).toLocaleTimeString('id-ID', {
                                hour: '2-digit',
                                minute: '2-digit',
                              })}
                            </p>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </>
            )}
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 p-4 lg:p-8 overflow-y-auto bg-slate-50">
          <div className="max-w-6xl mx-auto mb-8">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}

function NavItem({
  to,
  icon,
  children,
}: {
  to: string;
  icon: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        clsx(
          'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200',
          isActive
            ? 'bg-primary-50 text-primary-700 shadow-sm ring-1 ring-primary-100'
            : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900',
        )
      }
    >
      {icon}
      {children}
    </NavLink>
  );
}
