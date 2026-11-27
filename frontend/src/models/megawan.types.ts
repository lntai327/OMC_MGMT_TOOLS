export interface MegawanRecord {
  id: number;
  last_update?: string | null;
  expected_last_update?: string | null;
  expected_updated_at?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
  ma_tb?: string | null;
  ma_lt_ma_tb_sub?: string | null;
  ten_th_bao?: string | null;
  dia_chi?: string | null;
  diem_cuoi?: string | null;
  svlan_cvlan?: string | null;
  ten_thbi?: string | null;
  ip_thbi?: string | null;
  port_thbi?: string | null;
  upe?: string | null;
  ip_kh?: string | null;
  ip_gw?: string | null;
  loai_hinh_tb?: string | null;
  toc_do?: string | null;
  loai_kenh?: string | null;
  trang_thai?: string | null;
  cap_odf?: string | null;
  ghi_chu?: string | null;
}

export interface MegawanFilterParams {
  loai_hinh_tb?: string;
  ten_th_bao?: string;
  dia_chi?: string;
  loai_kenh?: string;
  svlan_cvlan?: string;
  ten_thbi?: string;
  all_search?: string;
}

export interface MegawanFieldOptions {
  loai_hinh_tb: string[];
  loai_kenh: string[];
  trang_thai: string[];
  ten_thbi: string[];
}

