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
          "id": SC.K_ID,
          "Mã TB": SC.K_MA_TB,
          "Mã LT/Mã TB SUB": SC.K_MA_LT_MA_TB_SUB,
          "Tên thuê bao": SC.K_TEN_TH_BAO,
          "Địa chỉ lắp đặt": SC.K_DIA_CHI,
          "Điểm cuối": SC.K_DIEM_CUOI,
          "SVLANCVLAN": SC.K_SVLAN_CVLAN,
          "Tên thiết bị": SC.K_TEN_THBI,
          "IP thiết bị": SC.K_IP_THBI,
          "Port thiết bị": SC.K_PORT_THBI,
          "UPE": SC.K_UPE,
          "IP KH": SC.K_IP_KH,
          "IP GW": SC.K_IP_GW,
          "Loại hình TB": SC.K_LOAI_HINH_TB,
          "Tốc độ": SC.K_TOC_DO,
          "Loại kênh": SC.K_LOAI_KENH,
          "Trạng thái": SC.K_TRANG_THAI,
          "Cáp ODF": SC.K_CAP_ODF,
          "Ghi chú": SC.K_GHI_CHU,
          "Ngày tác động": SC.K_LAST_UPDATE,
        }
      }
    },
    "hint": "ex: (abc).xlsx | sheet: (abc)"
  },
}