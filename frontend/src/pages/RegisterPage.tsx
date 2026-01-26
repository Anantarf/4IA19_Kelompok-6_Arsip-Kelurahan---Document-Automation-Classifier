import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { registerUser } from '../api/auth';
import {
  LayoutDashboard,
  Lock,
  User,
  ArrowRight,
  Loader2,
  ShieldCheck,
  AlertCircle,
} from 'lucide-react';

export default function RegisterPage() {
  const { register, handleSubmit } = useForm();
  const { login } = useAuth();
  const navigate = useNavigate();
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const onSubmit = async (data: any) => {
    setIsLoading(true);
    setError('');

    try {
      const authData = await registerUser(data.username, data.password);
      login(authData.access_token, { username: authData.username, role: authData.role });
      navigate('/');
    } catch (err: any) {
      if (err.response?.status === 400) {
        setError('Username sudah terdaftar');
      } else if (err.response?.status === 501) {
        setError('Fitur registrasi belum diaktifkan. Hubungi administrator.');
      } else {
        setError(err.response?.data?.detail || err.message || 'Gagal mendaftar. Coba lagi.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-card border border-slate-100 p-8 w-full max-w-md animate-fade-in">
        <div className="text-center mb-8">
          <img
            src="/logo-jakarta.png"
            alt="Logo DKI Jakarta"
            className="w-20 h-20 mx-auto mb-4 object-contain"
          />
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Registrasi Akun</h1>
          <p className="text-slate-700 mt-2 font-semibold leading-snug">Kelurahan Pela Mampang</p>
          <p className="text-slate-500 text-sm mt-2 leading-normal">
            Daftar untuk mulai mengelola dokumen
          </p>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1.5">Username</label>
            <div className="relative">
              <User className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
              <input
                {...register('username', { required: true })}
                className="w-full pl-10 pr-4 py-2.5 rounded-lg border border-slate-200 focus:border-primary-500 focus:ring-2 focus:ring-primary-100 outline-none transition-all"
                placeholder="Pilih username"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1.5">Password</label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
              <input
                type="password"
                {...register('password', { required: true })}
                className="w-full pl-10 pr-4 py-2.5 rounded-lg border border-slate-200 focus:border-primary-500 focus:ring-2 focus:ring-primary-100 outline-none transition-all"
                placeholder="Minimal 6 karakter"
              />
            </div>
          </div>

          {error && (
            <div className="p-3 bg-red-50 text-red-600 text-sm rounded-lg flex items-center gap-2">
              <AlertCircle size={16} /> {error}
            </div>
          )}

          <button
            type="submit"
            disabled={isLoading}
            className="w-full btn-primary py-2.5 flex items-center justify-center gap-2 mt-2"
          >
            {isLoading ? (
              <Loader2 className="animate-spin" size={20} />
            ) : (
              <>
                Daftar <ArrowRight size={18} />
              </>
            )}
          </button>
        </form>

        <p className="text-center text-sm text-slate-500 mt-6">
          Sudah punya akun?{' '}
          <Link to="/login" className="text-primary-600 font-medium hover:underline">
            Masuk disini
          </Link>
        </p>
      </div>
    </div>
  );
}
