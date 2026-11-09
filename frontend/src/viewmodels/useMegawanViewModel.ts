import { useState, useEffect, useCallback } from 'react';
import { MegawanRecord, MegawanFilterParams } from '../models/megawan.types';
import { PaginationParams } from '../models/common.types';
import { megawanService } from '../services/megawan.service';

export function useMegawanViewModel(onJobStarted?: (jobId: string, title: string, onCompleted?: () => void) => void) {
  const [records, setRecords] = useState<MegawanRecord[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [totalPages, setTotalPages] = useState<number>(1);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Pagination state
  const [pagination, setPagination] = useState<PaginationParams>({
    page: 1,
    page_size: 20,
    sort_by: 'id',
    sort_desc: true,
  });

  // Filter state
  const [filters, setFilters] = useState<MegawanFilterParams>({
    loai_hinh_tb: '',
    ten_th_bao: '',
    dia_chi: '',
    loai_kenh: '',
    svlan_cvlan: '',
    ten_he_thong: '',
    all_search: '',
  });

  // Selected record for editing / viewing
  const [selectedRecord, setSelectedRecord] = useState<MegawanRecord | null>(null);
  const [isFormModalOpen, setIsFormModalOpen] = useState<boolean>(false);
  const [isImportModalOpen, setIsImportModalOpen] = useState<boolean>(false);

  const fetchRecords = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await megawanService.getRecords(filters, pagination);
      setRecords(data.items);
      setTotal(data.total);
      setTotalPages(data.total_pages);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Không thể tải danh sách dữ liệu.');
    } finally {
      setLoading(false);
    }
  }, [filters, pagination]);

  useEffect(() => {
    fetchRecords();
  }, [fetchRecords]);

  const updateFilter = (key: keyof MegawanFilterParams, value: string) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
    setPagination((prev) => ({ ...prev, page: 1 }));
  };

  const clearFilters = () => {
    setFilters({
      loai_hinh_tb: '',
      ten_th_bao: '',
      dia_chi: '',
      loai_kenh: '',
      svlan_cvlan: '',
      ten_he_thong: '',
      all_search: '',
    });
    setPagination((prev) => ({ ...prev, page: 1 }));
  };

  const changePage = (page: number) => {
    setPagination((prev) => ({ ...prev, page }));
  };

  const changePageSize = (pageSize: number) => {
    setPagination((prev) => ({ ...prev, page_size: pageSize, page: 1 }));
  };

  const saveRecord = async (data: Partial<MegawanRecord>): Promise<boolean> => {
    setLoading(true);
    try {
      if (selectedRecord?.id) {
        await megawanService.update(selectedRecord.id, data);
      } else {
        await megawanService.create(data);
      }
      setIsFormModalOpen(false);
      setSelectedRecord(null);
      await fetchRecords();
      return true;
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Có lỗi xảy ra khi lưu bản ghi.');
      return false;
    } finally {
      setLoading(false);
    }
  };

  const deleteRecord = async (id: number): Promise<boolean> => {
    if (!window.confirm('Bạn có chắc chắn muốn xóa bản ghi này không?')) return false;
    setLoading(true);
    try {
      await megawanService.delete(id);
      await fetchRecords();
      return true;
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Có lỗi xảy ra khi xóa bản ghi.');
      return false;
    } finally {
      setLoading(false);
    }
  };

  const handleImportExcel = async (file: File) => {
    try {
      const res = await megawanService.importExcel(file);
      setIsImportModalOpen(false);
      if (onJobStarted) {
        // Pass fetchRecords as completion callback so table auto-refreshes when import finishes
        onJobStarted(res.job_id, 'Nhập dữ liệu Excel Megawan / Metronet', fetchRecords);
      }
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Lỗi nhập dữ liệu.');
    }
  };

  const handleExportExcel = async () => {
    try {
      const res = await megawanService.exportExcel(filters);
      if (onJobStarted) {
        onJobStarted(res.job_id, 'Xuất báo cáo Excel Megawan / Metronet');
      }
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Không thể khởi tạo tiến trình xuất báo cáo.');
    }
  };

  return {
    records,
    total,
    totalPages,
    loading,
    error,
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
  };
}

