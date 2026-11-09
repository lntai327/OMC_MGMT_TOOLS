import React, { useState } from 'react';
import { Search, Network, FileSpreadsheet, Activity, ChevronRight, CheckCircle2 } from 'lucide-react';
import { VnptLogo } from '../components/common/VnptLogo';

interface HomePageProps {
  onSelectReport: (route: string) => void;
}

interface ReportItem {
  id: string;
  name: string;
  description: string;
  icon: any;
  category: string;
  route: string;
  active: boolean;
  highlight?: string;
}

export const HomePage: React.FC<HomePageProps> = ({ onSelectReport }) => {
  const [search, setSearch] = useState('');

  const reports: ReportItem[] = [
    {
      id: 'megawan',
      name: 'Quản lý Megawan & Metronet',
      description: '',
      icon: Network,
      category: 'QNN',
      route: 'megawan',
      active: true,
      highlight: 'Demo',
    },
  ];

  const filteredReports = reports.filter((r) =>
    r.name.toLowerCase().includes(search.toLowerCase()) ||
    r.description.toLowerCase().includes(search.toLowerCase()) ||
    r.category.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="max-w-[1650px] mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Banner Chào mừng & Tìm kiếm */}
      <div className="bg-gradient-to-r from-vnpt-700 via-vnpt-600 to-vnpt-800 rounded-2xl p-8 sm:p-10 text-white shadow-xl relative overflow-hidden">
        <div className="relative z-10 max-w-3xl space-y-3">
          <div className="inline-flex items-center gap-2.5 px-4 py-2 bg-white/95 backdrop-blur-md rounded-full text-xs font-bold uppercase tracking-wider text-vnpt-800 border border-white shadow-sm">
            <VnptLogo height={20} />
            <span className="border-l border-slate-300 pl-2">Công cụ quản lý &amp; Báo cáo số liệu</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-black tracking-tight leading-tight">
            VNPT GIA LAI — OMC MANAGEMENT TOOL
          </h2>

          {/* Search Input lớn, dễ nhìn */}
          <div className="pt-4 max-w-2xl">
            <div className="relative flex items-center">
              <Search className="w-6 h-6 text-slate-400 absolute left-4 pointer-events-none z-10" />
              <input
                type="text"
                placeholder="Tìm kiếm chức năng..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full pl-12 pr-4 py-3.5 bg-white text-slate-900 border-2 border-transparent rounded-xl text-lg font-medium placeholder-slate-400 focus:outline-none focus:ring-4 focus:ring-vnpt-300 shadow-lg"
              />
            </div>
          </div>
        </div>

        {/* Trang trí nền mờ */}
        <div className="absolute -right-10 -bottom-10 opacity-15 pointer-events-none filter drop-shadow-xl">
          <VnptLogo height={240} className="rounded-2xl" />
        </div>
      </div>

      {/* Danh sách phân hệ chức năng */}
      <div>
        <div className="flex items-center justify-between mb-6">
          <div>
            <h3 className="text-2xl font-black text-slate-900 tracking-tight">
              CHỨC NĂNG
            </h3>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredReports.map((item) => {
            const Icon = item.icon;
            return (
              <div
                key={item.id}
                onClick={() => item.active && onSelectReport(item.route)}
                className={`relative bg-white rounded-2xl border-2 p-7 transition-all duration-200 flex flex-col justify-between ${item.active
                    ? 'border-vnpt-200 hover:border-vnpt-600 hover:shadow-xl cursor-pointer group hover:-translate-y-1'
                    : 'border-slate-200 opacity-60 cursor-not-allowed bg-slate-50'
                  }`}
              >
                <div>
                  <div className="flex items-center justify-between mb-5">
                    <div
                      className={`w-14 h-14 rounded-2xl flex items-center justify-center transition-colors shadow-sm ${item.active
                          ? 'bg-vnpt-100 text-vnpt-700 group-hover:bg-vnpt-600 group-hover:text-white'
                          : 'bg-slate-200 text-slate-400'
                        }`}
                    >
                      <Icon className="w-8 h-8" />
                    </div>
                    {item.active ? (
                      <span className="flex items-center gap-1.5 text-xs font-bold px-3 py-1 bg-emerald-100 text-emerald-800 rounded-full border border-emerald-200">
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        {item.highlight}
                      </span>
                    ) : (
                      <span className="text-xs font-bold px-3 py-1 bg-slate-200 text-slate-600 rounded-full">
                        Đang phát triển
                      </span>
                    )}
                  </div>

                  <div className="text-xs font-bold uppercase tracking-wider text-vnpt-600 mb-1">
                    {item.category}
                  </div>
                  <h4 className="text-xl font-bold text-slate-900 mb-2.5 group-hover:text-vnpt-700 transition-colors">
                    {item.name}
                  </h4>
                  <p className="text-base text-slate-600 leading-relaxed mb-6 font-normal">
                    {item.description}
                  </p>
                </div>

                <div className="pt-5 border-t-2 border-slate-100 flex items-center justify-between">
                  {item.active ? (
                    <span className="inline-flex items-center font-bold text-base text-vnpt-600 group-hover:text-vnpt-800 transition-colors">
                      Mở chức năng
                      <ChevronRight className="w-5 h-5 ml-1.5 group-hover:translate-x-1 transition-transform" />
                    </span>
                  ) : (
                    <span className="text-sm font-semibold text-slate-400 italic">
                      Đang phát triển
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};


