import React, { useState } from 'react';
import { Lock, User, AlertCircle, ShieldCheck, Eye, EyeOff } from 'lucide-react';
import { BrandLogo } from '../components/common/BrandLogo';
import { Button } from '../components/common/Button';
import { Input } from '../components/common/Input';

interface LoginPageProps {
  onLogin: (u: string, p: string) => Promise<boolean>;
  loading: boolean;
  error: string | null;
}

export const LoginPage: React.FC<LoginPageProps> = ({ onLogin, loading, error }) => {
  let df_user = "";
  let df_pw = "";
  df_user = "dev"
  df_pw = "" /*dev only*/

  const [username, setUsername] = useState(df_user);
  const [password, setPassword] = useState(df_pw);
  const [showPassword, setShowPassword] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await onLogin(username, password);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-100 via-brand-50 to-slate-200 flex flex-col justify-between p-4 sm:p-6">
      {/* Top Banner Branding */}
      <header className="max-w-6xl w-full mx-auto flex items-center justify-center py-4">
        <div className="flex items-center gap-4">
          <div className="bg-white p-1 rounded-xl shadow-sm border border-slate-200">
            <BrandLogo height={48} />
          </div>
          <div className="border-l-2 border-slate-300 pl-3.5">
            <div className="text-2xl font-bold text-slate-800 tracking-tight">VNPT GIA LAI</div>
          </div>
        </div>
      </header>

      {/* Main Login Card */}
      <main className="w-full max-w-lg mx-auto bg-white rounded-2xl shadow-xl border-2 border-slate-200 overflow-hidden my-auto">
        {/* Card Header */}
        <div className="bg-gradient-to-r from-brand-700 via-brand-600 to-brand-700 px-8 py-7 text-center text-white relative">
          <h2 className="text-2xl font-black tracking-tight uppercase">OMC MANAGEMENT TOOL</h2>
        </div>

        {/* Login Form */}
        <form onSubmit={handleSubmit} className="p-8 sm:p-10 space-y-6">
          {error && (
            <div className="flex items-start gap-3 p-4 bg-rose-50 border-2 border-rose-300 text-rose-800 text-base font-semibold rounded-xl">
              <AlertCircle className="w-6 h-6 flex-shrink-0 text-rose-600 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          <div className="space-y-2">
            <Input
              label="Tài khoản đăng nhập"
              placeholder="Nhập tên đăng nhập của bạn"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              autoFocus
              className="text-lg py-3"
            />
          </div>

          <div className="space-y-2">
            <Input
              label="Mật khẩu bảo mật"
              type={showPassword ? 'text' : 'password'}
              placeholder="Nhập mật khẩu"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="text-lg py-3"
              rightAction={
                <button
                  type="button"
                  onClick={() => setShowPassword((prev) => !prev)}
                  className="text-slate-400 hover:text-slate-600 focus:outline-none transition-colors p-1"
                  title={showPassword ? 'Ẩn mật khẩu' : 'Hiện mật khẩu'}
                  tabIndex={-1}
                >
                  {showPassword ? (
                    <EyeOff className="w-5 h-5" />
                  ) : (
                    <Eye className="w-5 h-5" />
                  )}
                </button>
              }
            />
          </div>

          <Button
            type="submit"
            variant="primary"
            size="lg"
            className="w-full py-3.5 text-lg font-bold shadow-lg shadow-brand-600/30"
            loading={loading}
          >
            ĐĂNG NHẬP VÀO HỆ THỐNG
          </Button>

          <div className="pt-2 text-center text-sm font-medium text-slate-500 border-t border-slate-100">
            Phiên bản 1.0.0
          </div>
        </form>
      </main>

      {/* Footer */}
      <footer className="text-center text-xs font-semibold text-slate-500 py-3">
        &copy; {new Date().getFullYear()} VNPT Gia Lai — OMC.
      </footer>
    </div>
  );
};


