import { apiClient } from './api.client';
import { MegawanRecord, MegawanFilterParams } from '../models/megawan.types';
import { PaginatedResponse, PaginationParams, MessageResponse } from '../models/common.types';
import { JobCreateResponse } from '../models/job.types';

export const megawanService = {
  async getRecords(
    filters: MegawanFilterParams,
    pagination: PaginationParams
  ): Promise<PaginatedResponse<MegawanRecord>> {
    const params: Record<string, any> = {
      page: pagination.page,
      page_size: pagination.page_size,
    };
    if (pagination.sort_by) params.sort_by = pagination.sort_by;
    if (pagination.sort_desc !== undefined) params.sort_desc = pagination.sort_desc;

    // Filters
    if (filters.loai_hinh_tb) params.loai_hinh_tb = filters.loai_hinh_tb;
    if (filters.ten_th_bao) params.ten_th_bao = filters.ten_th_bao;
    if (filters.dia_chi) params.dia_chi = filters.dia_chi;
    if (filters.loai_kenh) params.loai_kenh = filters.loai_kenh;
    if (filters.svlan_cvlan) params.svlan_cvlan = filters.svlan_cvlan;
    if (filters.ten_he_thong) params.ten_he_thong = filters.ten_he_thong;
    if (filters.all_search) params.all_search = filters.all_search;

    const response = await apiClient.get<PaginatedResponse<MegawanRecord>>('/megawan', { params });
    return response.data;
  },

  async getById(id: number): Promise<MegawanRecord> {
    const response = await apiClient.get<MegawanRecord>(`/megawan/${id}`);
    return response.data;
  },

  async create(record: Partial<MegawanRecord>): Promise<MegawanRecord> {
    const response = await apiClient.post<MegawanRecord>('/megawan', record);
    return response.data;
  },

  async update(id: number, record: Partial<MegawanRecord>): Promise<MegawanRecord> {
    const response = await apiClient.put<MegawanRecord>(`/megawan/${id}`, record);
    return response.data;
  },

  async delete(id: number): Promise<MessageResponse> {
    const response = await apiClient.delete<MessageResponse>(`/megawan/${id}`);
    return response.data;
  },

  async importExcel(file: File): Promise<JobCreateResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await apiClient.post<JobCreateResponse>('/megawan/import', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  async exportExcel(filters: MegawanFilterParams): Promise<JobCreateResponse> {
    const response = await apiClient.post<JobCreateResponse>('/megawan/export', filters);
    return response.data;
  },
};

