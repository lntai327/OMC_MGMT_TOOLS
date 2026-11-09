export interface MegawanRecord {
  id: number;
  last_update?: string | null;
  ma_tb?: string | null;
  ma_lt_ma_tb_sub?: string | null;
  ten_th_bao?: string | null;
  dia_chi?: string | null;
  diem_cuoi?: string | null;
  ip_src?: string | null;
  ip_des?: string | null;
  svlan_cvlan?: string | null;
  cap_adsl?: string | null;
  cap_odf?: string | null;
  ghi_chu?: string | null;
  ip?: string | null;
  ten_he_thong?: string | null;
  port_switch?: string | null;
  upe?: string | null;
  loai_hinh_tb?: string | null;
  trang_thai?: string | null;
  toc_do?: string | null;
  don_vi?: string | null;
  loai_kenh?: string | null;
}

export interface MegawanFilterParams {
  loai_hinh_tb?: string;
  ten_th_bao?: string;
  dia_chi?: string;
  loai_kenh?: string;
  svlan_cvlan?: string;
  ten_he_thong?: string;
  all_search?: string;
}

