from app.constant import constant as SC

EXCEL_STRUCT_INFO = {
  "excel_thbi_access": {
    "sheet_info": {
      "sheet_data": {
        "key": "sheet",
        "start_cell": "",
        "require_col_map": {}
      }
    },
    "hint": "ex: (abc)thiet bi access(abc).xlsx | sheet: Sheet(abc)"
  },

  "megawan_metronet": {
    "sheet_info": {
      "sheet_data": {
        "key": "",
        "start_cell": "ACTION",
        "require_col_map": {
          "ACTION": SC.K_ACTION,
          "MÃ TB": SC.K_MA_TB,
          "MÃ LT/MÃ TB SUB": SC.K_MA_LT_MA_TB_SUB,
          "Tên thuê bao": SC.K_TEN_TH_BAO,
          "Địa chỉ lắp đặt": SC.K_DIA_CHI,
          "id": SC.K_ID,
          "diemcuoi": SC.K_DIEM_CUOI,
          "ipsource": SC.K_IP_SRC,
          "ipdes": SC.K_IP_DES,
          "svlancvlan": SC.K_SVLAN_CVLAN,
          "capadsl": SC.K_CAP_ADSL,
          "capodf": SC.K_CAP_ODF,
          "ngaytacdong": SC.K_LAST_UPDATE,
          "ghichu": SC.K_GHI_CHU,
          "IP": SC.K_IP,
          "system": SC.K_TEN_HE_THONG,
          "portswitch": SC.K_PORT_SWITCH,
          "UPE": SC.K_UPE,
          "LOẠI HÌNH TB": SC.K_LOAI_HINH_TB,
          "Trạng thái": SC.K_TRANG_THAI,
          "Tốc độ": SC.K_TOC_DO,
          "Đơn vị": SC.K_DVI,
          "LOẠI KÊNH": SC.K_LOAI_KENH,
        }
      }
    },
    "hint": "ex: (abc).xlsx | sheet: (abc)"
  },
}