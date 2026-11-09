import React from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { Button } from './Button';

interface PaginationProps {
  currentPage: number;
  totalPages: number;
  totalItems: number;
  pageSize: number;
  onPageChange: (page: number) => void;
  onPageSizeChange: (pageSize: number) => void;
}

export const Pagination: React.FC<PaginationProps> = ({
  currentPage,
  totalPages,
  totalItems,
  pageSize,
  onPageChange,
  onPageSizeChange,
}) => {
  const startItem = totalItems === 0 ? 0 : (currentPage - 1) * pageSize + 1;
  const endItem = Math.min(currentPage * pageSize, totalItems);

  return (
    <div className="flex flex-col sm:flex-row items-center justify-between gap-4 px-6 py-4 bg-slate-50 border-t-2 border-slate-200 text-base text-slate-700">
      <div className="flex items-center gap-3">
        <span className="font-medium text-slate-700">Hiển thị:</span>
        <select
          value={pageSize}
          onChange={(e) => onPageSizeChange(Number(e.target.value))}
          className="border-2 border-slate-300 rounded-lg px-3 py-1.5 bg-white text-base font-bold text-slate-900 focus:border-vnpt-600 focus:ring-2 focus:ring-vnpt-300 focus:outline-none cursor-pointer"
        >
          <option value={10}>10</option>
          <option value={20}>20</option>
          <option value={50}>50</option>
          <option value={100}>100</option>
        </select>
        <span className="text-slate-600 font-medium">
          (Bản ghi <strong className="font-bold text-slate-900">{startItem}</strong> - <strong className="font-bold text-slate-900">{endItem}</strong> / Tổng cộng <strong className="text-vnpt-700 font-bold">{totalItems}</strong> bản ghi)
        </span>
      </div>

      <div className="flex items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={() => onPageChange(currentPage - 1)}
          disabled={currentPage <= 1}
          className="font-bold"
        >
          <ChevronLeft className="w-5 h-5 mr-1" />
          Trước
        </Button>
        <span className="px-4 py-1.5 font-bold text-base text-vnpt-900 bg-white border border-slate-300 rounded-lg shadow-sm">
          {currentPage} / {Math.max(1, totalPages)}
        </span>
        <Button
          variant="outline"
          size="sm"
          onClick={() => onPageChange(currentPage + 1)}
          disabled={currentPage >= totalPages}
          className="font-bold"
        >
          Sau
          <ChevronRight className="w-5 h-5 ml-1" />
        </Button>
      </div>
    </div>
  );
};


