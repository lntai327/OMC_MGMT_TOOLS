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
  { label: 'ID', width: 70 },
  { label: 'Mã TB', width: 130 },
  { label: 'Mã LT/Mã TB SUB', width: 155 },
  { label: 'Tên thuê bao', width: 220 },
  { label: 'Địa chỉ lắp đặt', width: 240 },
  { label: 'Điểm cuối', width: 150 },
  { label: 'SVLAN/CVLAN', width: 130 },
  { label: 'Tên thiết bị', width: 110 },
  { label: 'IP thiết bị', width: 140 },
  { label: 'Port thiết bị', width: 140 },
  { label: 'UPE', width: 100 },
  { label: 'IP KH', width: 140 },
  { label: 'IP GW', width: 140 },
  { label: 'Loại hình TB', width: 130 },
  { label: 'Tốc độ', width: 100 },
  { label: 'Loại kênh', width: 120 },
  { label: 'Trạng thái', width: 120 },
  { label: 'Cáp ODF', width: 110 },
  { label: 'Ghi chú', width: 160 },
  { label: 'Ngày tác động', width: 150 },
  { label: 'Thao tác', width: 112 }, // sticky action col – not resizable
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
    fieldOptions,
  } = useMegawanViewModel(onJobStarted);

  const [formData, setFormData] = useState<Partial<MegawanRecord>>({});
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [importType, setImportType] = useState<'megawan_metronet' | 'thbi_access'>('megawan_metronet');
  const [detailRecord, setDetailRecord] = useState<MegawanRecord | null>(null);
  const [isDetailModalOpen, setIsDetailModalOpen] = useState<boolean>(false);

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
      diem_cuoi: '', svlan_cvlan: '',
      ten_thbi: '', ip_thbi: '', port_thbi: '', upe: '',
      ip_kh: '', ip_gw: '', loai_hinh_tb: '',
      toc_do: '', loai_kenh: '',
      trang_thai: '',
      cap_odf: '', ghi_chu: '',
      last_update: '',
    });
    setIsFormModalOpen(true);
  };

  const openEditModal = (record: MegawanRecord) => {
    setSelectedRecord(record);
    setFormData({ ...record });
    setIsFormModalOpen(true);
  };

  const openDetailModal = (record: MegawanRecord) => {
    setDetailRecord(record);
    setIsDetailModalOpen(true);
  };

  const handleEditFromDetail = () => {
    if (detailRecord) {
      const rec = detailRecord;
      setIsDetailModalOpen(false);
      openEditModal(rec);
    }
  };

  const handleDeleteFromDetail = async () => {
    if (detailRecord) {
      const success = await deleteRecord(detailRecord.id);
      if (success) {
        setIsDetailModalOpen(false);
        setDetailRecord(null);
      }
    }
  };

  const handleFormSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await saveRecord(formData);
  };

  const handleImportSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (selectedFile) {
      await handleImportExcel(selectedFile, importType);
      setSelectedFile(null);
    }
  };

  const totalTableW = colWidths.reduce((a, b) => a + b, 0);
  const colSpanAll = COLUMNS.length;

  return (
    <div className="max-w-[1750px] mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-5">

      {/* 1. THANH TIÊU ĐỀ & THAO TÁC CHÍNH */}
      <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4 bg-white p-5 rounded-2xl border-2 border-slate-200 shadow-sm">
        <div className="flex items-center gap-4">
          <h2 className="text-2xl font-black text-brand-900 tracking-tight flex items-center gap-2">
            <Database className="w-7 h-7 text-brand-600" />
            QUẢN LÝ MEGAWAN &amp; METRONET
          </h2>
        </div>

        <div className="flex flex-wrap items-center gap-3 w-full lg:w-auto justify-end">
          {isOperator && (
            <Button variant="primary" size="md" onClick={openCreateModal}
              className="bg-brand-600 hover:bg-brand-700 shadow-md font-bold">
              <Plus className="w-5 h-5 mr-1.5" />
              Thêm bản ghi
            </Button>
          )}
          {isOperator && (
            <Button variant="outline" size="md" onClick={() => setIsImportModalOpen(true)}
              className="text-brand-700 border-brand-300 hover:bg-brand-50 hover:border-brand-500 font-bold">
              <Upload className="w-5 h-5 mr-1.5 text-brand-600" />
              Nhập Excel
            </Button>
          )}
          <Button variant="success" size="md" onClick={handleExportExcel} className="font-bold shadow-md">
            <Download className="w-5 h-5 mr-1.5" />
            Xuất Excel
          </Button>
          <Button variant="outline" size="md" onClick={fetchRecords} disabled={loading}
            title="Làm mới dữ liệu" className="font-bold">
            <RotateCcw className={`w-5 h-5 ${loading ? 'animate-spin text-brand-600' : ''}`} />
          </Button>
        </div>
      </div>

      {/* 2. KHUNG TÌM KIẾM & BỘ LỌC DỮ LIỆU */}
      <div className="bg-white p-6 rounded-2xl border-2 border-slate-200 shadow-sm space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-200">
          <div className="flex items-center gap-2.5 text-base font-black uppercase tracking-wide text-brand-800">
            <Filter className="w-5 h-5 text-brand-600" />
            BỘ LỌC
          </div>
          <button onClick={clearFilters}
            className="text-sm text-brand-600 hover:text-brand-800 font-bold underline cursor-pointer transition-colors">
            Hủy bộ lọc
          </button>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4">
          <div className="sm:col-span-2 md:col-span-2 lg:col-span-2">
            <Input label="Tìm kiếm Tất cả" placeholder="Nhập từ khóa cần tìm..."
              value={filters.all_search || ''}
              onChange={(e) => updateFilter('all_search', e.target.value)}
              className="border-brand-300 focus:border-brand-600 font-medium" />
          </div>
          <Input label="Loại hình TB" placeholder="Loại hình..."
            list="megawan-loai-hinh-tb-list"
            value={filters.loai_hinh_tb || ''} onChange={(e) => updateFilter('loai_hinh_tb', e.target.value)} />
          <Input label="Tên thuê bao" placeholder="Tên thuê bao..."
            value={filters.ten_th_bao || ''} onChange={(e) => updateFilter('ten_th_bao', e.target.value)} />
          <Input label="Địa chỉ lắp đặt" placeholder="Địa chỉ..."
            value={filters.dia_chi || ''} onChange={(e) => updateFilter('dia_chi', e.target.value)} />
          <Input label="Loại kênh" placeholder="Loại kênh..."
            list="megawan-loai-kenh-list"
            value={filters.loai_kenh || ''} onChange={(e) => updateFilter('loai_kenh', e.target.value)} />
          <Input label="Tên thiết bị" placeholder="Tên thiết bị..."
            list="megawan-ten-thbi-list"
            value={filters.ten_thbi || ''} onChange={(e) => updateFilter('ten_thbi', e.target.value)} />
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

            <thead className="bg-brand-50 text-brand-900 font-bold uppercase tracking-wide border-b-2 border-brand-200 sticky top-0 z-10 select-none">
              <tr>
                {COLUMNS.map((col, i) => {
                  const isAction = i === COLUMNS.length - 1;
                  return (
                    <th
                      key={i}
                      className={`py-4 px-3 whitespace-nowrap overflow-hidden text-ellipsis relative${isAction ? ' text-center sticky right-0 bg-brand-50 shadow-l' : ''
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
                          <span className="w-[2px] h-5 bg-brand-300 group-hover:bg-brand-600 rounded transition-colors" />
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
                      <div className="w-10 h-10 border-4 border-brand-600 border-t-transparent rounded-full animate-spin" />
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
                    onDoubleClick={() => openDetailModal(row)}
                    className={`transition-colors cursor-pointer select-none ${idx % 2 === 0 ? 'bg-white' : 'bg-slate-50/60'
                      } hover:bg-brand-50/70 group`}
                    title="Nhấp đúp chuột để xem chi tiết bản ghi"
                  >
                    <td className="py-3 px-3 overflow-hidden text-ellipsis whitespace-nowrap text-slate-700 font-medium">{row.id}</td>
                    <td className="py-3 px-3 overflow-hidden text-ellipsis whitespace-nowrap text-slate-700 font-medium">{row.ma_tb || '—'}</td>
                    <td className="py-3 px-3 overflow-hidden text-ellipsis whitespace-nowrap text-slate-700 font-medium">{row.ma_lt_ma_tb_sub || '—'}</td>
                    <td className="py-3 px-3 overflow-hidden text-ellipsis whitespace-nowrap text-slate-700 font-medium">{row.ten_th_bao || '—'}</td>
                    <td className="py-3 px-3 overflow-hidden text-ellipsis whitespace-nowrap text-slate-700 font-medium">{row.dia_chi || '—'}</td>
                    <td className="py-3 px-3 overflow-hidden text-ellipsis whitespace-nowrap text-slate-700 font-medium">{row.diem_cuoi || '—'}</td>
                    <td className="py-3 px-3 overflow-hidden text-ellipsis whitespace-nowrap text-slate-700 font-medium">{row.svlan_cvlan || '—'}</td>
                    <td className="py-3 px-3 overflow-hidden text-ellipsis whitespace-nowrap text-slate-700 font-medium">{row.ten_thbi || '—'}</td>
                    <td className="py-3 px-3 overflow-hidden text-ellipsis whitespace-nowrap text-slate-700 font-medium">{row.ip_thbi || '—'}</td>
                    <td className="py-3 px-3 overflow-hidden text-ellipsis whitespace-nowrap text-slate-700 font-medium">{row.port_thbi || '—'}</td>
                    <td className="py-3 px-3 overflow-hidden text-ellipsis whitespace-nowrap text-slate-700 font-medium">{row.upe || '—'}</td>
                    <td className="py-3 px-3 overflow-hidden text-ellipsis whitespace-nowrap text-slate-700 font-medium">{row.ip_kh || '—'}</td>
                    <td className="py-3 px-3 overflow-hidden text-ellipsis whitespace-nowrap text-slate-700 font-medium">{row.ip_gw || '—'}</td>
                    <td className="py-3 px-3 overflow-hidden text-ellipsis whitespace-nowrap text-slate-700 font-medium">{row.loai_hinh_tb || '—'}</td>
                    <td className="py-3 px-3 overflow-hidden text-ellipsis whitespace-nowrap text-slate-700 font-medium">{row.toc_do || '—'}</td>
                    <td className="py-3 px-3 overflow-hidden text-ellipsis whitespace-nowrap text-slate-700 font-medium">{row.loai_kenh || '—'}</td>
                    <td className="py-3 px-3 overflow-hidden text-ellipsis whitespace-nowrap text-slate-700 font-medium">{row.trang_thai || '—'}</td>
                    <td className="py-3 px-3 overflow-hidden text-ellipsis whitespace-nowrap text-slate-700 font-medium">{row.cap_odf || '—'}</td>
                    <td className="py-3 px-3 overflow-hidden text-ellipsis whitespace-nowrap text-slate-700 font-medium">{row.ghi_chu || '—'}</td>
                    <td className="py-3 px-3 overflow-hidden text-ellipsis whitespace-nowrap text-slate-700 font-medium">{row.last_update || '—'}</td>
                    <td className="py-3 px-3 text-center sticky right-0 bg-white group-hover:bg-brand-50/70 transition-colors shadow-l">
                      <div className="flex items-center justify-center gap-2">
                        {isOperator && (
                          <button onClick={(e) => { e.stopPropagation(); openEditModal(row); }}
                            className="p-2 text-brand-600 hover:text-white hover:bg-brand-600 rounded-lg transition-colors border border-brand-200"
                            title="Chỉnh sửa">
                            <Edit2 className="w-4 h-4" />
                          </button>
                        )}
                        {isAdmin && (
                          <button onClick={(e) => { e.stopPropagation(); deleteRecord(row.id); }}
                            className="p-2 text-rose-600 hover:text-white hover:bg-rose-600 rounded-lg transition-colors border border-rose-200"
                            title="Xóa">
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
          : 'Thêm bản ghi'}
        maxWidth="2xl"
      >
        <form onSubmit={handleFormSubmit} className="space-y-5">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="sm:col-span-2">
              <Input label="Tên thuê bao" value={formData.ten_th_bao || ''}
                onChange={(e) => setFormData({ ...formData, ten_th_bao: e.target.value })} />
            </div>
            <div className="sm:col-span-2">
              <Input label="Địa chỉ lắp đặt" value={formData.dia_chi || ''}
                onChange={(e) => setFormData({ ...formData, dia_chi: e.target.value })} />
            </div>
            <div className="sm:col-span-2">
              <Input label="Điểm cuối" value={formData.diem_cuoi || ''}
                onChange={(e) => setFormData({ ...formData, diem_cuoi: e.target.value })} />
            </div>

            <Input label="Mã TB" value={formData.ma_tb || ''}
              onChange={(e) => setFormData({ ...formData, ma_tb: e.target.value })} />
            <Input label="Mã LT/Mã TB Sub" value={formData.ma_lt_ma_tb_sub || ''}
              onChange={(e) => setFormData({ ...formData, ma_lt_ma_tb_sub: e.target.value })} />

            <Input label="Loại hình TB" value={formData.loai_hinh_tb || ''}
              list="megawan-loai-hinh-tb-list"
              placeholder="Chọn hoặc nhập loại hình..."
              onChange={(e) => setFormData({ ...formData, loai_hinh_tb: e.target.value })} />
            <Input label="Loại kênh" value={formData.loai_kenh || ''}
              list="megawan-loai-kenh-list"
              placeholder="Chọn hoặc nhập loại kênh..."
              onChange={(e) => setFormData({ ...formData, loai_kenh: e.target.value })} />

            <div className="sm:col-span-2">
              <Input label="Tốc độ" value={formData.toc_do || ''}
                onChange={(e) => setFormData({ ...formData, toc_do: e.target.value })} />
            </div>

            <Input label="Tên thiết bị" value={formData.ten_thbi || ''}
              list="megawan-ten-thbi-list"
              placeholder="Chọn hoặc nhập tên thiết bị..."
              onChange={(e) => setFormData({ ...formData, ten_thbi: e.target.value })} />
            <Input label="UPE" value={formData.upe || ''}
              onChange={(e) => setFormData({ ...formData, upe: e.target.value })} />

            <div className="sm:col-span-2">
              <Input label="SVLAN/CVLAN" value={formData.svlan_cvlan || ''}
                onChange={(e) => setFormData({ ...formData, svlan_cvlan: e.target.value })} />
            </div>

            <Input label="IP thiết bị" value={formData.ip_thbi || ''}
              onChange={(e) => setFormData({ ...formData, ip_thbi: e.target.value })} />
            <Input label="Port thiết bị" value={formData.port_thbi || ''}
              onChange={(e) => setFormData({ ...formData, port_thbi: e.target.value })} />

            <Input label="IP KH" value={formData.ip_kh || ''}
              onChange={(e) => setFormData({ ...formData, ip_kh: e.target.value })} />
            <Input label="IP GW" value={formData.ip_gw || ''}
              onChange={(e) => setFormData({ ...formData, ip_gw: e.target.value })} />

            <div className="sm:col-span-2">
              <Input label="Cáp ODF" value={formData.cap_odf || ''}
                onChange={(e) => setFormData({ ...formData, cap_odf: e.target.value })} />
            </div>

            <div className="sm:col-span-2">
              <Input label="Trạng thái" value={formData.trang_thai || ''}
                list="megawan-trang-thai-list"
                placeholder="Chọn hoặc nhập trạng thái..."
                onChange={(e) => setFormData({ ...formData, trang_thai: e.target.value })} />
            </div>

            <div className="sm:col-span-2">
              <Input label="Ghi chú" value={formData.ghi_chu || ''}
                onChange={(e) => setFormData({ ...formData, ghi_chu: e.target.value })} />
            </div>

          </div>

          <div className="flex justify-center gap-3 pt-5 border-t-2 border-slate-100">
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
        onClose={() => {
          setIsImportModalOpen(false);
          setSelectedFile(null);
        }}
        title="Nhập dữ liệu Excel"
        maxWidth="lg"
      >
        <form onSubmit={handleImportSubmit} className="space-y-5 text-center py-2">
          {/* Lựa chọn loại dữ liệu import */}
          <div className="text-left space-y-2">
            <label className="block text-sm font-bold text-slate-700">Chọn dữ liệu nhập:</label>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <button
                type="button"
                onClick={() => setImportType('megawan_metronet')}
                className={`p-3.5 rounded-xl border-2 text-left transition-all ${
                  importType === 'megawan_metronet'
                    ? 'border-brand-600 bg-brand-50/60 text-brand-900 shadow-sm'
                    : 'border-slate-200 hover:border-slate-300 text-slate-700 bg-white'
                }`}
              >
                <div className="font-bold text-sm flex items-center justify-between">
                  <span>Megawan-Metronet</span>
                  {importType === 'megawan_metronet' && (
                    <span className="w-2.5 h-2.5 rounded-full bg-brand-600 inline-block"></span>
                  )}
                </div>
                <div className="text-xs text-slate-500 mt-1">Cập nhật theo ACTION (INSERT / DELETE)</div>
              </button>

              <button
                type="button"
                onClick={() => setImportType('thbi_access')}
                className={`p-3.5 rounded-xl border-2 text-left transition-all ${
                  importType === 'thbi_access'
                    ? 'border-brand-600 bg-brand-50/60 text-brand-900 shadow-sm'
                    : 'border-slate-200 hover:border-slate-300 text-slate-700 bg-white'
                }`}
              >
                <div className="font-bold text-sm flex items-center justify-between">
                  <span>Thiết bị OLT</span>
                  {importType === 'thbi_access' && (
                    <span className="w-2.5 h-2.5 rounded-full bg-brand-600 inline-block"></span>
                  )}
                </div>
                <div className="text-xs text-slate-500 mt-1">Cập nhật theo Tên hệ thống</div>
              </button>
            </div>
          </div>

          <div className="border-3 border-dashed border-brand-300 rounded-2xl p-8 hover:border-brand-600 transition-colors bg-brand-50/40">
            <FileSpreadsheet className="w-14 h-14 text-brand-600 mx-auto mb-3" />
            <h4 className="text-base font-bold text-slate-800 mb-1">
              {selectedFile ? selectedFile.name : 'Chọn file Excel (.xlsx, .xls)'}
            </h4>
            <input type="file" id="excel-file-input" accept=".xlsx, .xls" className="hidden"
              onChange={(e) => { if (e.target.files?.[0]) setSelectedFile(e.target.files[0]); }} />
            <label htmlFor="excel-file-input"
              className="inline-flex items-center px-5 py-2.5 bg-brand-600 text-white rounded-xl text-sm font-bold hover:bg-brand-700 cursor-pointer shadow-md shadow-brand-600/30 transition-all hover:scale-[1.02] mt-2">
              Chọn tệp tin Excel...
            </label>
          </div>
          <div className="flex justify-center gap-3">
            <Button variant="outline" size="md" type="button" onClick={() => {
              setIsImportModalOpen(false);
              setSelectedFile(null);
            }}>
              Hủy
            </Button>
            <Button variant="primary" size="md" type="submit" disabled={!selectedFile}
              className="font-bold bg-brand-600 hover:bg-brand-700">
              Bắt đầu nhập dữ liệu
            </Button>
          </div>
        </form>
      </Modal>

      {/* 6. MODAL XEM CHI TIẾT BẢN GHI (KHI DOUBLE CLICK VÀO DÒNG DỮ LIỆU) */}
      <Modal
        isOpen={isDetailModalOpen && !!detailRecord}
        onClose={() => {
          setIsDetailModalOpen(false);
          setDetailRecord(null);
        }}
        title={`Chi tiết bản ghi #${detailRecord?.id || ''}`}
        maxWidth="2xl"
      >
        {detailRecord && (
          <div className="space-y-5">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 max-h-[60vh] overflow-y-auto pr-1">
              <Input
                label="ID"
                value={detailRecord.id ?? ''}
                readOnly
                className="bg-slate-50 text-slate-800 cursor-default"
              />
              <Input
                label="Ngày tác động"
                value={detailRecord.last_update || '—'}
                readOnly
                className="bg-slate-50 text-slate-800 cursor-default"
              />

              <div className="sm:col-span-2">
                <Input
                  label="Tên thuê bao"
                  value={detailRecord.ten_th_bao || '—'}
                  readOnly
                  className="bg-slate-50 text-slate-800 cursor-default"
                />
              </div>
              <div className="sm:col-span-2">
                <Input
                  label="Địa chỉ lắp đặt"
                  value={detailRecord.dia_chi || '—'}
                  readOnly
                  className="bg-slate-50 text-slate-800 cursor-default"
                />
              </div>
              <div className="sm:col-span-2">
                <Input
                  label="Điểm cuối"
                  value={detailRecord.diem_cuoi || '—'}
                  readOnly
                  className="bg-slate-50 text-slate-800 cursor-default"
                />
              </div>

              <Input
                label="Mã TB"
                value={detailRecord.ma_tb || '—'}
                readOnly
                className="bg-slate-50 text-slate-800 cursor-default"
              />
              <Input
                label="Mã LT/Mã TB Sub"
                value={detailRecord.ma_lt_ma_tb_sub || '—'}
                readOnly
                className="bg-slate-50 text-slate-800 cursor-default"
              />

              <Input
                label="Loại hình TB"
                value={detailRecord.loai_hinh_tb || '—'}
                readOnly
                className="bg-slate-50 text-slate-800 cursor-default"
              />
              <Input
                label="Loại kênh"
                value={detailRecord.loai_kenh || '—'}
                readOnly
                className="bg-slate-50 text-slate-800 cursor-default"
              />

              <div className="sm:col-span-2">
                <Input
                  label="Tốc độ"
                  value={detailRecord.toc_do || '—'}
                  readOnly
                  className="bg-slate-50 text-slate-800 cursor-default"
                />
              </div>

              <Input
                label="Tên thiết bị"
                value={detailRecord.ten_thbi || '—'}
                readOnly
                className="bg-slate-50 text-slate-800 cursor-default"
              />
              <Input
                label="UPE"
                value={detailRecord.upe || '—'}
                readOnly
                className="bg-slate-50 text-slate-800 cursor-default"
              />

              <div className="sm:col-span-2">
                <Input
                  label="SVLAN/CVLAN"
                  value={detailRecord.svlan_cvlan || '—'}
                  readOnly
                  className="bg-slate-50 text-slate-800 cursor-default"
                />
              </div>

              <Input
                label="IP thiết bị"
                value={detailRecord.ip_thbi || '—'}
                readOnly
                className="bg-slate-50 text-slate-800 cursor-default"
              />
              <Input
                label="Port thiết bị"
                value={detailRecord.port_thbi || '—'}
                readOnly
                className="bg-slate-50 text-slate-800 cursor-default"
              />

              <Input
                label="IP KH"
                value={detailRecord.ip_kh || '—'}
                readOnly
                className="bg-slate-50 text-slate-800 cursor-default"
              />
              <Input
                label="IP GW"
                value={detailRecord.ip_gw || '—'}
                readOnly
                className="bg-slate-50 text-slate-800 cursor-default"
              />

              <div className="sm:col-span-2">
                <Input
                  label="Cap ODF"
                  value={detailRecord.cap_odf || '—'}
                  readOnly
                  className="bg-slate-50 text-slate-800 cursor-default"
                />
              </div>

              <div className="sm:col-span-2">
                <Input
                  label="Trạng thái"
                  value={detailRecord.trang_thai || '—'}
                  readOnly
                  className="bg-slate-50 text-slate-800 cursor-default"
                />
              </div>

              <div className="sm:col-span-2">
                <Input
                  label="Ghi chú"
                  value={detailRecord.ghi_chu || '—'}
                  readOnly
                  className="bg-slate-50 text-slate-800 cursor-default"
                />
              </div>
            </div>

            <div className="flex justify-center items-center gap-3 pt-5 border-t-2 border-slate-100">
              {isOperator && (
                <Button
                  variant="primary"
                  size="md"
                  type="button"
                  onClick={handleEditFromDetail}
                  className="font-bold bg-brand-600 hover:bg-brand-700"
                >
                  <Edit2 className="w-4 h-4 mr-1.5" />
                  Chỉnh sửa
                </Button>
              )}
              {isAdmin && (
                <Button
                  variant="danger"
                  size="md"
                  type="button"
                  onClick={handleDeleteFromDetail}
                  loading={loading}
                  className="font-bold bg-rose-600 hover:bg-rose-700"
                >
                  <Trash2 className="w-4 h-4 mr-1.5" />
                  Xóa
                </Button>
              )}
            </div>
          </div>
        )}
      </Modal>

      {/* 7. DATALISTS CHO GỢI Ý DROPDOWN (LẤY TỪ DB) */}
      <datalist id="megawan-loai-hinh-tb-list">
        {fieldOptions.loai_hinh_tb.map((opt) => (
          <option key={`opt-lh-${opt}`} value={opt} />
        ))}
      </datalist>

      <datalist id="megawan-loai-kenh-list">
        {fieldOptions.loai_kenh.map((opt) => (
          <option key={`opt-lk-${opt}`} value={opt} />
        ))}
      </datalist>

      <datalist id="megawan-trang-thai-list">
        {fieldOptions.trang_thai.map((opt) => (
          <option key={`opt-tt-${opt}`} value={opt} />
        ))}
      </datalist>

      <datalist id="megawan-ten-thbi-list">
        {fieldOptions.ten_thbi?.map((opt) => (
          <option key={`opt-thbi-${opt}`} value={opt} />
        ))}
      </datalist>
    </div>
  );
};
