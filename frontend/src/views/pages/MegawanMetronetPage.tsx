import React, { useState, useRef, useCallback } from 'react';
import {
  Plus,
  Upload,
  Download,
  RotateCcw,
  Edit2,
  Trash2,
  Filter,
  ArrowLeft,
  FileSpreadsheet,
  Database,
} from 'lucide-react';
import { Button } from '../components/common/Button';
import { Input } from '../components/common/Input';
import { Modal } from '../components/common/Modal';
import { Pagination } from '../components/common/Pagination';
import { MegawanRecord } from '../../models/megawan.types';
import { useMegawanViewModel } from '../../viewmodels/useMegawanViewModel';

interface MegawanPageProps {
  onBack: () => void;
  onJobStarted: (jobId: string, title: string, onCompleted?: () => void) => void;
  isOperator: boolean;
  isAdmin: boolean;
}

// Column definitions: label + default width (px)
const COLUMNS: { label: string; width: number }[] = [
  { label: 'ID',               width: 70  },
  { label: 'Mã TB',            width: 130 },
  { label: 'Mã LT / Mã TB Sub', width: 155 },
  { label: 'Tên thuê bao',     width: 220 },
  { label: 'Địa chỉ lắp đặt', width: 240 },
  { label: 'Điểm cuối',        width: 150 },
  { label: 'IP Src',           width: 120 },
  { label: 'IP Des',           width: 120 },
  { label: 'SVLAN / CVLAN',    width: 130 },
  { label: 'Cap ADSL',         width: 110 },
  { label: 'Cap ODF',          width: 110 },
  { label: 'Ghi chú',          width: 160 },
  { label: 'IP / Subnet',      width: 140 },
  { label: 'Hệ thống',         width: 130 },
  { label: 'Port Switch',      width: 120 },
  { label: 'UPE',              width: 100 },
  { label: 'Loại hình TB',     width: 130 },
  { label: 'Trạng thái',       width: 120 },
  { label: 'Tốc độ',           width: 100 },
  { label: 'Đơn vị',           width: 90  },
  { label: 'Loại kênh',        width: 120 },
  { label: 'Cập nhật lúc',     width: 150 },
  { label: 'Thao tác',         width: 112 }, // sticky action col – not resizable
];

export const MegawanMetronetPage: React.FC<MegawanPageProps> = ({
  onBack,
  onJobStarted,
  isOperator,
  isAdmin,
}) => {
  const {
    records,
    total,
    totalPages,
    loading,
    filters,
    pagination,
    selectedRecord,
    isFormModalOpen,
    isImportModalOpen,
    setSelectedRecord,
    setIsFormModalOpen,
    setIsImportModalOpen,
    updateFilter,
    clearFilters,
    changePage,
    changePageSize,
    fetchRecords,
    saveRecord,
    deleteRecord,
    handleImportExcel,
    handleExportExcel,
  } = useMegawanViewModel(onJobStarted);

  const [formData, setFormData] = useState<Partial<MegawanRecord>>({});
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  // ── Resizable columns ──────────────────────────────────────────────────────
  const [colWidths, setColWidths] = useState<number[]>(COLUMNS.map((c) => c.width));
  const resizingCol = useRef<number | null>(null);
  const resizeStartX = useRef<number>(0);
  const resizeStartW = useRef<number>(0);

  const onResizeMouseDown = useCallback(
    (e: React.MouseEvent, colIdx: number) => {
      e.preventDefault();
      resizingCol.current = colIdx;
      resizeStartX.current = e.clientX;
      resizeStartW.current = colWidths[colIdx];

      const onMouseMove = (ev: MouseEvent) => {
        if (resizingCol.current === null) return;
        const delta = ev.clientX - resizeStartX.current;
        const newW = Math.max(60, resizeStartW.current + delta);
        setColWidths((prev) => {
          const next = [...prev];
          next[resizingCol.current!] = newW;
          return next;
        });
      };

      const onMouseUp = () => {
        resizingCol.current = null;
        window.removeEventListener('mousemove', onMouseMove);
        window.removeEventListener('mouseup', onMouseUp);
      };

      window.addEventListener('mousemove', onMouseMove);
      window.addEventListener('mouseup', onMouseUp);
    },
    [colWidths],
  );

  // ── Modal helpers ──────────────────────────────────────────────────────────
  const openCreateModal = () => {
    setSelectedRecord(null);
    setFormData({
      ma_tb: '', ma_lt_ma_tb_sub: '', ten_th_bao: '', dia_chi: '',
      diem_cuoi: '', ip_src: '', ip_des: '', svlan_cvlan: '',
      cap_adsl: '', cap_odf: '', ghi_chu: '', ip: '',
      ten_he_thong: '', port_switch: '', upe: '', loai_hinh_tb: '',
      trang_thai: '', toc_do: '', don_vi: '', loai_kenh: '',
    });
    setIsFormModalOpen(true);
  };

  const openEditModal = (record: MegawanRecord) => {
    setSelectedRecord(record);
    setFormData({ ...record });
    setIsFormModalOpen(true);
  };

  const handleFormSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await saveRecord(formData);
  };

  const handleImportSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (selectedFile) {
      await handleImportExcel(selectedFile);
      setSelectedFile(null);
    }
  };

  const totalTableW = colWidths.reduce((a, b) => a + b, 0);
  const colSpanAll  = COLUMNS.length;

  return (
    <div className="max-w-[1750px] mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-5">

      {/* 1. THANH TIÊU ĐỀ & THAO TÁC CHÍNH */}
      <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4 bg-white p-5 rounded-2xl border-2 border-slate-200 shadow-sm">
        <div className="flex items-center gap-4">
          <Button variant="outline" size="md" onClick={onBack} className="font-bold">
            <ArrowLeft className="w-5 h-5 mr-1" />
            Về Trang chủ
          </Button>
          <div className="border-l-2 border-slate-200 pl-4">
            <h2 className="text-2xl font-black text-vnpt-900 tracking-tight flex items-center gap-2">
              <Database className="w-7 h-7 text-vnpt-600" />
              QUẢN LÝ DỮ LIỆU MEGAWAN &amp; METRONET
            </h2>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3 w-full lg:w-auto justify-end">
          {isOperator && (
            <Button variant="primary" size="md" onClick={openCreateModal}
              className="bg-vnpt-600 hover:bg-vnpt-700 shadow-md font-bold">
              <Plus className="w-5 h-5 mr-1.5" />
              Thêm bản ghi mới
            </Button>
          )}
          {isOperator && (
            <Button variant="outline" size="md" onClick={() => setIsImportModalOpen(true)}
              className="text-vnpt-700 border-vnpt-300 hover:bg-vnpt-50 hover:border-vnpt-500 font-bold">
              <Upload className="w-5 h-5 mr-1.5 text-vnpt-600" />
              Nhập Excel
            </Button>
          )}
          <Button variant="success" size="md" onClick={handleExportExcel} className="font-bold shadow-md">
            <Download className="w-5 h-5 mr-1.5" />
            Xuất file Excel
          </Button>
          <Button variant="outline" size="md" onClick={fetchRecords} disabled={loading}
            title="Làm mới dữ liệu" className="font-bold">
            <RotateCcw className={`w-5 h-5 ${loading ? 'animate-spin text-vnpt-600' : ''}`} />
          </Button>
        </div>
      </div>

      {/* 2. KHUNG TÌM KIẾM & BỘ LỌC DỮ LIỆU */}
      <div className="bg-white p-6 rounded-2xl border-2 border-slate-200 shadow-sm space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-200">
          <div className="flex items-center gap-2.5 text-base font-black uppercase tracking-wide text-vnpt-800">
            <Filter className="w-5 h-5 text-vnpt-600" />
            BỘ LỌC TÌM KIẾM DỮ LIỆU CHI TIẾT
          </div>
          <button onClick={clearFilters}
            className="text-sm text-vnpt-600 hover:text-vnpt-800 font-bold underline cursor-pointer transition-colors">
            Hủy bộ lọc
          </button>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4">
          <div className="sm:col-span-2 md:col-span-2 lg:col-span-2">
            <Input label="Tìm kiếm Tất cả" placeholder="Nhập từ khóa cần tìm..."
              value={filters.all_search || ''}
              onChange={(e) => updateFilter('all_search', e.target.value)}
              className="border-vnpt-300 focus:border-vnpt-600 font-medium" />
          </div>
          <Input label="Loại hình TB" placeholder="Loại hình..."
            value={filters.loai_hinh_tb || ''} onChange={(e) => updateFilter('loai_hinh_tb', e.target.value)} />
          <Input label="Tên thuê bao" placeholder="Tên thuê bao..."
            value={filters.ten_th_bao || ''} onChange={(e) => updateFilter('ten_th_bao', e.target.value)} />
          <Input label="Địa chỉ lắp đặt" placeholder="Địa chỉ..."
            value={filters.dia_chi || ''} onChange={(e) => updateFilter('dia_chi', e.target.value)} />
          <Input label="Loại kênh" placeholder="Loại kênh..."
            value={filters.loai_kenh || ''} onChange={(e) => updateFilter('loai_kenh', e.target.value)} />
          <Input label="Tên hệ thống" placeholder="Tên hệ thống..."
            value={filters.ten_he_thong || ''} onChange={(e) => updateFilter('ten_he_thong', e.target.value)} />
        </div>
      </div>

      {/* 3. BẢNG DỮ LIỆU CHÍNH */}
      <div className="bg-white rounded-2xl border-2 border-slate-200 shadow-sm overflow-hidden flex flex-col">
        {/*
          Two-axis scroll:
          - overflow-x-auto  → horizontal scroll when table wider than viewport
          - overflow-y-auto  → vertical scroll when rows exceed max-height
          - max-height: 70vh → table body never grows taller than 70% of viewport
          Sticky thead works because the scroll container itself scrolls (not the page).
        */}
        <div className="overflow-x-auto overflow-y-auto" style={{ maxHeight: '70vh' }}>
          <table
            className="text-left text-[14.5px] border-collapse"
            style={{ tableLayout: 'fixed', width: totalTableW }}
          >
            {/* <colgroup> drives actual column widths in fixed layout */}
            <colgroup>
              {colWidths.map((w, i) => <col key={i} style={{ width: w }} />)}
            </colgroup>

            <thead className="bg-vnpt-50 text-vnpt-900 font-bold uppercase tracking-wide border-b-2 border-vnpt-200 sticky top-0 z-10 select-none">
              <tr>
                {COLUMNS.map((col, i) => {
                  const isAction = i === COLUMNS.length - 1;
                  return (
                    <th
                      key={i}
                      className={`py-4 px-3 whitespace-nowrap overflow-hidden text-ellipsis relative${
                        isAction ? ' text-center sticky right-0 bg-vnpt-50 shadow-l' : ''
                      }`}
                      style={{ width: colWidths[i] }}
                    >
                      {col.label}
                      {/* Drag-resize handle — only on data columns, not action column */}
                      {!isAction && (
                        <span
                          onMouseDown={(e) => onResizeMouseDown(e, i)}
                          title="Kéo để thay đổi chiều rộng cột"
                          style={{ userSelect: 'none' }}
                          className="absolute top-0 right-0 h-full w-2 cursor-col-resize flex items-center justify-center group z-20"
                        >
                          <span className="w-[2px] h-5 bg-vnpt-300 group-hover:bg-vnpt-600 rounded transition-colors" />
                        </span>
                      )}
                    </th>
                  );
                })}
              </tr>
            </thead>

            <tbody className="divide-y divide-slate-200">
              {loading && records.length === 0 ? (
                <tr>
                  <td colSpan={colSpanAll} className="py-16 text-center text-slate-500 text-base font-medium">
                    <div className="flex flex-col items-center justify-center gap-3">
                      <div className="w-10 h-10 border-4 border-vnpt-600 border-t-transparent rounded-full animate-spin" />
                      <span>Đang tải dữ liệu...</span>
                    </div>
                  </td>
                </tr>
              ) : records.length === 0 ? (
                <tr>
                  <td colSpan={colSpanAll} className="py-16 text-center text-slate-500 text-base font-medium">
                    Không tìm thấy bản ghi nào phù hợp với bộ lọc tìm kiếm.
                  </td>
                </tr>
              ) : (
                records.map((row, idx) => (
                  <tr
                    key={row.id}
                    className={`transition-colors cursor-default ${
                      idx % 2 === 0 ? 'bg-white' : 'bg-slate-50/60'
                    } hover:bg-vnpt-50/70 group`}
                  >
                    <td className="py-3 px-3 overflow-hidden text-ellipsis whitespace-nowrap text-slate-500 font-mono text-[13px]">{row.id}</td>
                    <td className="py-3 px-3 overflow-hidden text-ellipsis whitespace-nowrap font-bold text-vnpt-800 font-mono">{row.ma_tb || '—'}</td>
                    <td className="py-3 px-3 overflow-hidden text-ellipsis whitespace-nowrap text-slate-700 font-medium">{row.ma_lt_ma_tb_sub || '—'}</td>
                    <td className="py-3 px-3 overflow-hidden text-ellipsis whitespace-nowrap font-bold text-slate-900">{row.ten_th_bao || '—'}</td>
                    <td className="py-3 px-3 overflow-hidden text-ellipsis whitespace-nowrap text-slate-700 font-medium" title={row.dia_chi || ''}>{row.dia_chi || '—'}</td>
                    <td className="py-3 px-3 overflow-hidden text-ellipsis whitespace-nowrap text-slate-700 font-medium">{row.diem_cuoi || '—'}</td>
                    <td className="py-3 px-3 overflow-hidden text-ellipsis whitespace-nowrap text-slate-700 font-mono">{row.ip_src || '—'}</td>
                    <td className="py-3 px-3 overflow-hidden text-ellipsis whitespace-nowrap text-slate-700 font-mono">{row.ip_des || '—'}</td>
                    <td className="py-3 px-3 overflow-hidden text-ellipsis whitespace-nowrap text-slate-800 font-mono font-semibold">{row.svlan_cvlan || '—'}</td>
                    <td className="py-3 px-3 overflow-hidden text-ellipsis whitespace-nowrap text-slate-700 font-medium">{row.cap_adsl || '—'}</td>
                    <td className="py-3 px-3 overflow-hidden text-ellipsis whitespace-nowrap text-slate-700 font-medium">{row.cap_odf || '—'}</td>
                    <td className="py-3 px-3 overflow-hidden text-ellipsis whitespace-nowrap text-slate-600" title={row.ghi_chu || ''}>{row.ghi_chu || '—'}</td>
                    <td className="py-3 px-3 overflow-hidden text-ellipsis whitespace-nowrap text-slate-800 font-mono font-semibold">{row.ip || '—'}</td>
                    <td className="py-3 px-3 overflow-hidden text-ellipsis whitespace-nowrap text-slate-700 font-medium">{row.ten_he_thong || '—'}</td>
                    <td className="py-3 px-3 overflow-hidden text-ellipsis whitespace-nowrap text-slate-700 font-medium">{row.port_switch || '—'}</td>
                    <td className="py-3 px-3 overflow-hidden text-ellipsis whitespace-nowrap text-slate-700 font-mono font-semibold">{row.upe || '—'}</td>
                    <td className="py-3 px-3 overflow-hidden whitespace-nowrap">
                      <span className="inline-block px-2.5 py-1 rounded-md text-xs font-bold bg-vnpt-100 text-vnpt-800 border border-vnpt-200">
                        {row.loai_hinh_tb || '—'}
                      </span>
                    </td>
                    <td className="py-3 px-3 overflow-hidden text-ellipsis whitespace-nowrap text-slate-700 font-medium">{row.trang_thai || '—'}</td>
                    <td className="py-3 px-3 overflow-hidden text-ellipsis whitespace-nowrap text-slate-800 font-bold">{row.toc_do || '—'}</td>
                    <td className="py-3 px-3 overflow-hidden text-ellipsis whitespace-nowrap text-slate-700 font-medium">{row.don_vi || '—'}</td>
                    <td className="py-3 px-3 overflow-hidden text-ellipsis whitespace-nowrap text-slate-700 font-medium">{row.loai_kenh || '—'}</td>
                    <td className="py-3 px-3 overflow-hidden text-ellipsis whitespace-nowrap text-slate-500 text-xs font-medium">{row.last_update || '—'}</td>
                    <td className="py-3 px-3 text-center sticky right-0 bg-white group-hover:bg-vnpt-50/70 transition-colors shadow-l">
                      <div className="flex items-center justify-center gap-2">
                        {isOperator && (
                          <button onClick={() => openEditModal(row)}
                            className="p-2 text-vnpt-600 hover:text-white hover:bg-vnpt-600 rounded-lg transition-colors border border-vnpt-200"
                            title="Chỉnh sửa bản ghi">
                            <Edit2 className="w-4 h-4" />
                          </button>
                        )}
                        {isAdmin && (
                          <button onClick={() => deleteRecord(row.id)}
                            className="p-2 text-rose-600 hover:text-white hover:bg-rose-600 rounded-lg transition-colors border border-rose-200"
                            title="Xóa bản ghi">
                            <Trash2 className="w-4 h-4" />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Thanh phân trang */}
        <Pagination
          currentPage={pagination.page}
          totalPages={totalPages}
          totalItems={total}
          pageSize={pagination.page_size}
          onPageChange={changePage}
          onPageSizeChange={changePageSize}
        />
      </div>

      {/* 4. MODAL THÊM / CHỈNH SỬA BẢN GHI */}
      <Modal
        isOpen={isFormModalOpen}
        onClose={() => setIsFormModalOpen(false)}
        title={selectedRecord
          ? `Chỉnh sửa bản ghi ID #${selectedRecord.id}`
          : 'Thêm mới bản ghi Megawan / Metronet'}
        maxWidth="2xl"
      >
        <form onSubmit={handleFormSubmit} className="space-y-5">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input label="Mã Thuê Bao (*)" value={formData.ma_tb || ''} required
              onChange={(e) => setFormData({ ...formData, ma_tb: e.target.value })} />
            <Input label="Mã LT / Mã TB Sub" value={formData.ma_lt_ma_tb_sub || ''}
              onChange={(e) => setFormData({ ...formData, ma_lt_ma_tb_sub: e.target.value })} />
            <div className="sm:col-span-2">
              <Input label="Tên thuê bao (*)" value={formData.ten_th_bao || ''} required
                onChange={(e) => setFormData({ ...formData, ten_th_bao: e.target.value })} />
            </div>
            <div className="sm:col-span-2">
              <Input label="Địa chỉ lắp đặt" value={formData.dia_chi || ''}
                onChange={(e) => setFormData({ ...formData, dia_chi: e.target.value })} />
            </div>
            <Input label="Điểm cuối" value={formData.diem_cuoi || ''}
              onChange={(e) => setFormData({ ...formData, diem_cuoi: e.target.value })} />
            <Input label="IP Src" value={formData.ip_src || ''}
              onChange={(e) => setFormData({ ...formData, ip_src: e.target.value })} />
            <Input label="IP Des" value={formData.ip_des || ''}
              onChange={(e) => setFormData({ ...formData, ip_des: e.target.value })} />
            <Input label="SVLAN / CVLAN" value={formData.svlan_cvlan || ''}
              onChange={(e) => setFormData({ ...formData, svlan_cvlan: e.target.value })} />
            <Input label="Cap ADSL" value={formData.cap_adsl || ''}
              onChange={(e) => setFormData({ ...formData, cap_adsl: e.target.value })} />
            <Input label="Cap ODF" value={formData.cap_odf || ''}
              onChange={(e) => setFormData({ ...formData, cap_odf: e.target.value })} />
            <div className="sm:col-span-2">
              <Input label="Ghi chú" value={formData.ghi_chu || ''}
                onChange={(e) => setFormData({ ...formData, ghi_chu: e.target.value })} />
            </div>
            <Input label="IP / Subnet" value={formData.ip || ''}
              onChange={(e) => setFormData({ ...formData, ip: e.target.value })} />
            <Input label="Tên hệ thống" value={formData.ten_he_thong || ''}
              onChange={(e) => setFormData({ ...formData, ten_he_thong: e.target.value })} />
            <Input label="Port Switch" value={formData.port_switch || ''}
              onChange={(e) => setFormData({ ...formData, port_switch: e.target.value })} />
            <Input label="UPE" value={formData.upe || ''}
              onChange={(e) => setFormData({ ...formData, upe: e.target.value })} />
            <Input label="Loại hình TB" value={formData.loai_hinh_tb || ''}
              onChange={(e) => setFormData({ ...formData, loai_hinh_tb: e.target.value })} />
            <Input label="Trạng thái" value={formData.trang_thai || ''}
              onChange={(e) => setFormData({ ...formData, trang_thai: e.target.value })} />
            <Input label="Tốc độ" value={formData.toc_do || ''}
              onChange={(e) => setFormData({ ...formData, toc_do: e.target.value })} />
            <Input label="Đơn vị" value={formData.don_vi || ''}
              onChange={(e) => setFormData({ ...formData, don_vi: e.target.value })} />
            <Input label="Loại kênh" value={formData.loai_kenh || ''}
              onChange={(e) => setFormData({ ...formData, loai_kenh: e.target.value })} />
          </div>

          <div className="flex justify-end gap-3 pt-5 border-t-2 border-slate-100">
            <Button variant="outline" size="md" type="button" onClick={() => setIsFormModalOpen(false)}>
              Hủy bỏ
            </Button>
            <Button variant="primary" size="md" type="submit" loading={loading} className="font-bold">
              Lưu bản ghi
            </Button>
          </div>
        </form>
      </Modal>

      {/* 5. MODAL IMPORT FILE EXCEL */}
      <Modal
        isOpen={isImportModalOpen}
        onClose={() => setIsImportModalOpen(false)}
        title="Nhập dữ liệu Excel Megawan & Metronet"
        maxWidth="lg"
      >
        <form onSubmit={handleImportSubmit} className="space-y-6 text-center py-2">
          <div className="border-3 border-dashed border-vnpt-300 rounded-2xl p-10 hover:border-vnpt-600 transition-colors bg-vnpt-50/40">
            <FileSpreadsheet className="w-16 h-16 text-vnpt-600 mx-auto mb-4" />
            <h4 className="text-lg font-bold text-slate-800 mb-1">
              {selectedFile ? selectedFile.name : 'Chọn file Excel từ máy tính (.xlsx, .xls)'}
            </h4>
            <input type="file" id="excel-file-input" accept=".xlsx, .xls" className="hidden"
              onChange={(e) => { if (e.target.files?.[0]) setSelectedFile(e.target.files[0]); }} />
            <label htmlFor="excel-file-input"
              className="inline-flex items-center px-6 py-3 bg-vnpt-600 text-white rounded-xl text-base font-bold hover:bg-vnpt-700 cursor-pointer shadow-md shadow-vnpt-600/30 transition-all hover:scale-[1.02]">
              Chọn tệp tin Excel...
            </label>
          </div>
          <div className="flex justify-center gap-3">
            <Button variant="outline" size="md" type="button" onClick={() => setIsImportModalOpen(false)}>
              Hủy
            </Button>
            <Button variant="primary" size="md" type="submit" disabled={!selectedFile}
              className="font-bold bg-vnpt-600 hover:bg-vnpt-700">
              Bắt đầu nhập dữ liệu
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
