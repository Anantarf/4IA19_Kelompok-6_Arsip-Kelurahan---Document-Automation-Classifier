import React, { useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { createUser, deleteUser, listUsers, resetUserPassword } from '../api/users';
import { useAuth } from '../contexts/AuthContext';
import { useNotification } from '../contexts/NotificationContext';
import { KeyRound, Trash2, UserPlus } from 'lucide-react';

export default function AdminUsersPage() {
  const { user } = useAuth();
  const { addNotification } = useNotification();
  const qc = useQueryClient();

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState<'admin' | 'staf'>('staf');

  const { data: users = [], isLoading } = useQuery(['admin-users'], listUsers, {
    enabled: user?.role === 'admin',
  });

  const createMutation = useMutation(createUser, {
    onSuccess: () => {
      qc.invalidateQueries(['admin-users']);
      setUsername('');
      setPassword('');
      setRole('staf');
      addNotification('Pengguna berhasil ditambahkan');
    },
    onError: (err: any) => {
      addNotification(err?.response?.data?.detail || 'Gagal menambahkan pengguna');
    },
  });

  const deleteMutation = useMutation(deleteUser, {
    onSuccess: () => {
      qc.invalidateQueries(['admin-users']);
      addNotification('Pengguna berhasil dihapus');
    },
    onError: (err: any) => {
      addNotification(err?.response?.data?.detail || 'Gagal menghapus pengguna');
    },
  });

  const resetMutation = useMutation(
    ({ userId, password }: { userId: number; password: string }) =>
      resetUserPassword(userId, password),
    {
      onSuccess: () => {
        addNotification('Password berhasil direset');
      },
      onError: (err: any) => {
        addNotification(err?.response?.data?.detail || 'Gagal reset password');
      },
    },
  );

  const canSubmit = useMemo(() => username.trim() && password.trim(), [username, password]);

  if (user?.role !== 'admin') {
    return (
      <div className="max-w-7xl mx-auto animate-fade-in">
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
          <h1 className="text-2xl font-bold text-slate-900">Kelola Pengguna</h1>
          <p className="text-slate-500 mt-2">Halaman ini hanya untuk admin.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto animate-fade-in space-y-6">
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
        <h1 className="text-3xl font-bold text-slate-900 tracking-tight">Kelola Pengguna</h1>
        <p className="text-slate-600 text-sm mt-2 font-normal leading-relaxed">
          Tambah, lihat, dan hapus akun pengguna.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
          <h2 className="text-base sm:text-lg font-semibold text-slate-900 mb-4">
            Tambah Pengguna
          </h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Username</label>
              <input
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-200 focus:border-blue-400"
                placeholder="contoh: staf1"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Password</label>
              <input
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                type="password"
                className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-200 focus:border-blue-400"
                placeholder="Minimal 6 karakter"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Peran</label>
              <select
                value={role}
                onChange={(e) => setRole(e.target.value as 'admin' | 'staf')}
                className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-200 focus:border-blue-400"
              >
                <option value="staf">Staf</option>
                <option value="admin">Admin</option>
              </select>
            </div>
            <button
              onClick={() => createMutation.mutate({ username: username.trim(), password, role })}
              disabled={!canSubmit || createMutation.isLoading}
              className="btn-primary w-full flex items-center justify-center gap-2 py-2.5 text-sm"
            >
              <UserPlus size={16} />
              {createMutation.isLoading ? 'Menyimpan...' : 'Tambah Pengguna'}
            </button>
          </div>
        </div>

        <div className="lg:col-span-2 bg-white rounded-xl shadow-sm border border-slate-200 p-6">
          <h2 className="text-base sm:text-lg font-semibold text-slate-900 mb-4">
            Daftar Pengguna
          </h2>
          {isLoading ? (
            <p className="text-sm text-slate-500">Sedang memuat pengguna...</p>
          ) : users.length === 0 ? (
            <p className="text-sm text-slate-500">Belum ada pengguna.</p>
          ) : (
            <div className="overflow-x-auto max-h-[420px] overflow-y-auto">
              <table className="w-full">
                <thead className="bg-slate-50 border-b border-slate-100">
                  <tr>
                    <th className="text-left py-3 px-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                      Username
                    </th>
                    <th className="text-left py-3 px-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                      Peran
                    </th>
                    <th className="text-right py-3 px-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                      Aksi
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {users.map((u) => (
                    <tr key={u.id} className="hover:bg-slate-50 transition-colors">
                      <td className="py-3 px-4 text-sm text-slate-900">{u.username}</td>
                      <td className="py-3 px-4">
                        <span
                          className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                            u.role === 'admin'
                              ? 'bg-blue-100 text-blue-800'
                              : 'bg-slate-100 text-slate-700'
                          }`}
                        >
                          {u.role === 'admin' ? 'Admin' : 'Staf'}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right space-x-1">
                        <button
                          onClick={() => {
                            const newPassword = prompt(
                              `Reset password untuk ${u.username}. Masukkan password baru:`,
                            );
                            if (!newPassword) return;
                            resetMutation.mutate({ userId: u.id, password: newPassword });
                          }}
                          className="p-2 rounded-lg text-slate-500 hover:text-blue-600 hover:bg-blue-50"
                          title="Reset password"
                        >
                          <KeyRound size={16} />
                        </button>
                        <button
                          onClick={() => deleteMutation.mutate(u.id)}
                          className="p-2 rounded-lg text-slate-500 hover:text-red-600 hover:bg-red-50"
                          title="Hapus pengguna"
                        >
                          <Trash2 size={16} />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
