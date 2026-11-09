import React from 'react';
import { LogOut, User as UserIcon, ShieldCheck, Home, Network, FileSpreadsheet, Activity, HelpCircle } from 'lucide-react';
import { VnptLogo } from '../common/VnptLogo';
import { Button } from '../common/Button';

interface NavbarProps {
  currentUser: { username: string; role: string } | null;
  onLogout: () => void;
  onNavigateHome: () => void;
  currentView: string;
  onSelectView?: (view: 'home' | 'megawan') => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  currentUser,
  onLogout,
  onNavigateHome,
  currentView,
  onSelectView,
}) => {
  const handleNav = (view: 'home' | 'megawan') => {
    if (onSelectView) {
      onSelectView(view);
    } else if (view === 'home') {
      onNavigateHome();
    }
  };

  return (
    <header className="sticky top-0 z-40 shadow-md">
      {/* 1. TOP BAR: Màu trắng, Logo VNPT, Tên chi nhánh, Tìm kiếm nhanh & Tài khoản */}
      <div className="bg-white border-b border-slate-200">
        <div className="max-w-[1650px] mx-auto px-4 sm:px-6 lg:px-8 h-20 flex items-center justify-between">
          {/* Logo & Brand Info */}
          <div className="flex items-center gap-6">
            <div
              onClick={() => handleNav('home')}
              className="flex items-center gap-4 cursor-pointer select-none group"
            >
              <div className="bg-white p-1 rounded-lg">
                <VnptLogo height={44} className="transition-transform group-hover:scale-105" />
              </div>
              <div className="border-l-2 border-slate-200 pl-3.5">
                <div className="flex items-baseline gap-2">
                  <span className="text-xl font-bold text-slate-800 tracking-tight">VNPT GIA LAI</span>
                </div>
                <div className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                  OMC
                </div>
              </div>
            </div>
          </div>

          {/* User Status & Logout */}
          {currentUser && (
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-3 px-4 py-2 bg-slate-50 rounded-xl border border-slate-200 shadow-sm">
                <div className="w-9 h-9 rounded-full bg-vnpt-100 text-vnpt-700 flex items-center justify-center font-bold">
                  <UserIcon className="w-5 h-5" />
                </div>
                <div className="text-left">
                  <div className="text-sm font-bold text-slate-900 leading-tight">
                    {currentUser.username}
                  </div>
                  <div className="flex items-center gap-1.5 text-xs font-semibold text-vnpt-700 mt-0.5">
                    <ShieldCheck className="w-3.5 h-3.5 text-vnpt-600" />
                    <span>Quyền: {currentUser.role}</span>
                  </div>
                </div>
              </div>

              <Button
                variant="outline"
                size="sm"
                onClick={onLogout}
                className="text-rose-700 border-rose-200 hover:bg-rose-50 hover:border-rose-300 font-bold"
              >
                <LogOut className="w-4 h-4 mr-1.5" />
                Đăng xuất
              </Button>
            </div>
          )}
        </div>
      </div>

      {/* 2. MAIN BLUE MENU BAR (Đúng chuẩn nhận diện VNPT với dải menu xanh đậm) */}
      <div className="bg-gradient-to-r from-vnpt-700 via-vnpt-600 to-vnpt-700 text-white shadow-inner">
        <div className="max-w-[1650px] mx-auto px-4 sm:px-6 lg:px-8">
          <nav className="flex items-center space-x-1 overflow-x-auto py-1">
            {/* Tab Trang chủ */}
            <button
              onClick={() => handleNav('home')}
              className={`flex items-center gap-2.5 px-5 py-3 rounded-lg font-bold text-base transition-all duration-150 whitespace-nowrap ${
                currentView === 'home'
                  ? 'bg-white text-vnpt-700 shadow-md transform scale-[1.02]'
                  : 'text-white/90 hover:bg-white/15 hover:text-white'
              }`}
            >
              <Home className="w-5 h-5" />
              <span>TRANG CHỦ</span>
            </button>

            {/* Tab Quản lý Megawan / Metronet */}
            <button
              onClick={() => handleNav('megawan')}
              className={`flex items-center gap-2.5 px-5 py-3 rounded-lg font-bold text-base transition-all duration-150 whitespace-nowrap ${
                currentView === 'megawan'
                  ? 'bg-white text-vnpt-700 shadow-md transform scale-[1.02]'
                  : 'text-white/90 hover:bg-white/15 hover:text-white'
              }`}
            >
              <Network className="w-5 h-5" />
              <span>MEGAWAN &amp; METRONET</span>
            </button>
          </nav>
        </div>
      </div>
    </header>
  );
};


