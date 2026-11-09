EXCEL_STRUCT_INFO = {
  "excel_csht_ccl": {
    "sheet_info": {
      "sheet_csht_mdsd": {
        "start_cell": "Mã CSHT",
        "require_col": [
            "Mã CSHT", "Tên CSHT", "Tên Đơn vị Quản lý", "Trạng thái",
            "Tên TTVT/Trạm viễn thông NETx", "Loại nhà trạm", "Phường xã", "Địa chỉ",
            "Trạng thái đặt máy nổ", "Mã loại CSHT di dộng",
          ]
      }
    },
    "hint": "ex: csht_ccl(abc).xlsx | sheet: Sheet(abc)"
  },

  "excel_tht_ttvt": {
    "sheet_info": {
      "sheet_ttvt": {
        "start_cell": "site",
        "require_col": ["site", "ttvt", "to_ha_tang"]
      }
    },
    "hint": "ex: to_ha_tang_ttvt(abc).xlsx | sheet: ttvt(abc)"
  },

  "excel_cell_3g": {
    "sheet_info": {
      "sheet_cell3g": {
        "start_cell": "Trạng thái hoạt động",
        "require_col": ["Trạng thái hoạt động", "Tên trên hệ thống", "Mã CSHT CỦA CELL",
                        "Mã CSHT CỦA TRẠM", "Loại đối tượng", "Địa chỉ", "Tên quản lý",
                        "Tên đơn vị"]
      }
    },
    "hint": "ex: CELL_3G(abc).xlsx | sheet: CELL_3G(abc)"
  },

  "excel_cell_4g": {
    "sheet_info": {
      "sheet_cell4g": {
        "start_cell": "Loại đối tượng",
        "require_col": ["Loại đối tượng", "Tên trên hệ thống", "Mã CSHT CỦA CELL",
                        "Mã CSHT CỦA TRẠM", "Địa chỉ", "Tên quản lý", "Tên đơn vị",
                        "Trạng thái hoạt động"]
      }
    },
    "hint": "ex: CELL_4G(abc).xlsx | sheet: CELL_4G(abc)"
  },

  "excel_cell_5g": {
    "sheet_info": {
      "sheet_cell5g": {
        "start_cell": "Loại đối tượng",
        "require_col": ["Loại đối tượng", "Tên trên hệ thống", "Mã CSHT",
                        "Địa chỉ", "Tên quản lý", "Trạng thái hoạt động", "Tên đơn vị"]
      }
    },
    "hint": "ex: CELL5G(abc).xlsx | sheet: CELL5G(abc)"
  },

  "excel_bc_cell_mll": {
    "sheet_info": {
      "BÁO CÁO TỔNG HỢP": {
        "start_cell": "",
        "require_col": [""]
      },
      "TH CELL MLL theo CSHT": {
        "start_cell": "STT",
        "require_col": ["STT", "Mã CSHT CỦA CELL", "Vị trí cell so với vị trí đặt BBU",
                        "Mã trạm", "Cell 3G hiện có",
                        "Cell 3G mll", "Cell 4G hiện có", "Cell 4G mll",
                        "Cell 5G hiện có", "Cell 5G mll", "Tổng cell",
                        "Tổng cell mll", "Tên CSHT", "Địa chỉ CSHT", "TTVT"]
      },
      "Chi tiết TTVT X": {
        "start_cell": "STT",
        "require_col": ["STT", "Mã CSHT Cell", "LOẠI NE", "TÊN NE",
                        "TÊN GỢI NHỚ", "TG sự cố", "Nguyên nhân", "TTVT", "Tổ hạ tầng",
                        "Phân loại trạm"]
      }
    }
  },

  "excel_rp_al_bc_cell_mll": {
    "sheet_info": {
      "sheet_data": {
        "start_cell": "LOẠI NE",
        "require_col": ["LOẠI NE", "TÊN NE", "TG SỰ CỐ", "N.NHÂN",
                        "QUẬN/HUYỆN", "PHÂN LOẠI TRẠM"]
      }
    },
    "hint": "ex: ReportAlarm(abc).xlsx | sheet: DATA(abc)"
  },

  "excel_nodeb_3g": {
    "sheet_info": {
      "sheet_nodeb_3g": {
        "start_cell": "Trạng thái hoạt động",
        "require_col": [
          "Trạng thái hoạt động", "Mã CSHT", "Tên trên hệ thống", "Tên quản lý",
          "Trạng thái đặt máy nổ", "Loại trạm",
          "Băng tần",	"Ngày kiểm duyệt", "Service IP", "OAM IP",
        ]
      }
    },
    "hint": "ex: (abc)site_3g(abc).xlsx | sheet: Data(abc)"
  },

  "excel_enodeb_4g": {
    "sheet_info": {
      "sheet_enodeb_4g": {
        "start_cell": "Trạng thái hoạt động",
        "require_col": [
          "Trạng thái hoạt động", "Mã CSHT", "Tên trên hệ thống", "Tên quản lý",
          "Trạng thái đặt máy nổ", "Loại trạm",
          "Băng tần",	"Ngày kiểm duyệt", "Service IP", "OAM IP",
        ]
      }
    },
    "hint": "ex: (abc)site_4g(abc).xlsx | sheet: Data(abc)"
  },

  "excel_gnodeb_5g": {
    "sheet_info": {
      "sheet_gnodeb_5g": {
        "start_cell": "Trạng thái hoạt động",
        "require_col": [
          "Trạng thái hoạt động", "Mã CSHT", "Tên trên hệ thống", "Tên quản lý"
          "Loại trạm",
          "Băng tần",	"Ngày kiểm duyệt", "Service IP", "OAM IP",
          "IP GW OAM 5G", "SERVICE_IP_GW", "5G service VLAN",	"OAM_VLAN",
        ]
      }
    },
    "hint": "ex: (abc)site_5g(abc).xlsx | sheet: Data(abc)"
  },

  "excel_rp_al_bc_chay_mpd_qua_bgs": {
    "sheet_info": {
      "sheet_data": {
        "start_cell": "TÊN NE",
        "require_col": [
            "TÊN NE",	"TG SỰ CỐ", "TG CLR", "TG C.BÁO", "T.THÁI CLR",	"VNP-GHI CHÚ", "TỈNH GHI CHÚ",
            "LOẠI SỰ CỐ", "PHÂN LOẠI TRẠM", "TIME AC", "HỆ THỐNG", "ĐƠN VỊ QUẢN LÝ",
        ]
      }
    },
    "hint": "ex: ReportAlarm(abc).xlsx | sheet: DATA(abc)"
  },

  "excel_bc_chay_mpd_qua_bgs": {
    "sheet_info": {
      "BÁO CÁO TỔNG HỢP": {
        "start_cell": "",
        "require_col": [""]
      },
      "BC Chi Tiết": {
        "start_cell": "STT",
        "require_col": ["STT", "ĐƠN VỊ QUẢN LÝ", "TTVT", "NE", "Tên trạm", "Thời gian sự cố",
                          "Thời gian CLR", "Thời gian CB", "VNP - Ghi chú", "Tỉnh Ghi chú",
                          "Loại\nsự cố", "Thời gian\ncảnh báo AC", "Phân loại trạm"]
      },
      "CANHBAO_NCLR": {
        "start_cell": "STT",
        "require_col": ["STT", "ĐƠN VỊ QUẢN LÝ", "TTVT", "NE", "Tên trạm", "Thời gian sự cố",
                          "Thời gian CLR", "Thời gian CB", "VNP - Ghi chú", "Tỉnh Ghi chú",
                          "Loại\nsự cố", "Thời gian\ncảnh báo AC", "Phân loại trạm", "Ghi chú"]
      }
    }
  },

  "excel_dmoi_qly_csht": {
    "sheet_info": {
      "sheet_dmoi_qly_csht": {
        "start_cell": "Mã CSHT",
        "require_col": ["Mã CSHT", "Phân cấp", "Họ và Tên"]
      }
    },
    "hint": "ex: Đầu mối quản lý CSHT(abc).xlsx | sheet: Sheet(abc)"
  },

  "excel_dmoi_qly_csht_1": {
    "sheet_info": {
      "sheet_data": {
        "start_cell": "Mã CSHT",
        "require_col": ["Mã CSHT", "Họ và tên", "Tên hệ thống", "Đơn vị", "Vai trò"]
      }
    },
    "hint": "ex: DanhSachDauMoi(abc).xlsx | sheet: DATA(abc)"
  },

  "excel_rp_al_bc_cbao_mll": {
    "sheet_info": {
      "sheet_data": {
        "start_cell": "TÊN NE",
        "require_col": [
          "TT", "MỨC", "LOẠI NE", "TÊN NE",
          "TÊN GỢI NHỚ","OBJECT", "BSC/RNC",
          "N.NHÂN","NHÀ CC", "TG SỰ CỐ",
          "TG CLR", "TG C.BÁO", "T.THÁI CLR", "MÃ CB",
          "CHI TIẾT", "TỈNH/TP", "QUẬN/HUYỆN", "VNP-GHI CHÚ",
          "TỈNH GHI CHÚ", "LOẠI SỰ CỐ", "PHÂN LOẠI TRẠM", "TIME AC",
          "HỆ THỐNG", "GLOBALID", "TG TẠO TRÊN FMS", "ĐƠN VỊ QUẢN LÝ",
        ]
      }
    },
    "hint": "ex: ReportAlarm(abc).xlsx | sheet: DATA(abc)"
  },

  "excel_bc_cbao_mll": {
    "sheet_info": {
      "BÁO CÁO TỔNG HỢP": {
        "start_cell": "",
        "require_col": [""]
      },
      "Biểu Đồ Thống Kê": {
        "start_cell": "",
        "require_col": [""]
      },
      "BC MLL_nguồn(trừL3_KoMPĐ)-TD": {
        "start_cell": "STT",
        "require_col": ["STT", "TTVT", "NE", "Tên trạm", "Thời gian sự cố", "Thời gian CLR",
                          "Thời gian CB", "VNP - Ghi chú", "Tỉnh Ghi chú",
                          "Loại\nsự cố", "Thời gian\ncảnh báo AC",
                          "Phân loại trạm", "Trạng thái đặt máy nổ", "CSHT", "Tổ hạ tầng", "Nhân viên hạ tầng"]
      },
      "BC chi tiết MLL_tất cả các NN": {
        "start_cell": "STT",
        "require_col": ["STT", "TTVT", "NE", "Tên trạm", "Thời gian sự cố", "Thời gian CLR",
                          "Thời gian CB", "VNP - Ghi chú", "Tỉnh Ghi chú",
                          "Loại\nsự cố", "Thời gian\ncảnh báo AC",
                          "Phân loại trạm", "Trạng thái đặt máy nổ", "CSHT", "Tổ hạ tầng", "Nhân viên hạ tầng"]
      }
    }
  },

  "bc_cbao_mll_nclr": {
    "sheet_info": {
      "BÁO CÁO TỔNG HỢP": {
        "start_cell": "",
        "require_col": [""]
      },
      "CANHBAO_MATAC": {
        "start_cell": "STT",
        "require_col": ["STT", "TTVT", "NE", "Hệ thống", "Tên trạm", "Thời gian sự cố", "VNP - Ghi chú", "Tỉnh Ghi chú", "Phân loại trạm", "Trạng thái đặt máy nổ", "CSHT", "Tổ hạ tầng", "Nhân viên hạ tầng"]
      },
      "CSHT Mất liên lạc": {
        "start_cell": "STT",
        "require_col": ["STT", "Mã CSHT", "Tên CSHT", "Địa chỉ", "Phường xã", "N.NHÂN", "Thời gian sự cố", "TTVT", "Phân loại trạm", "Mã trạm", "Mã loại CSHT di dộng", "Trạng thái đặt máy nổ", "Tổ hạ tầng", "Nhân viên hạ tầng"]
      },
      "MLL BTS TTVT X": {
        "start_cell": "STT",
        "require_col": ["STT", "TTVT", "NE", "Hệ thống", "Tên trạm", "Thời gian sự cố", "VNP - Ghi chú", "Tỉnh Ghi chú", "Phân loại trạm", "Trạng thái đặt máy nổ", "CSHT", "Tổ hạ tầng", "Nhân viên hạ tầng"]
      }
    }
  },

  "excel_qly_hsuat_xgspon": {
    "sheet_info": {
      "sheet_data": {
        "start_cell": "STT",
        "require_col": [
            "STT", "Mã tỉnh", "Địa điểm", "Loại", "Quận/Huyện", "Đơn vị", "Tên hệ thống",
            "IP", "Số lượng card XGSPON", "Vị trí card", "Tên Card", "SL Port",
            "SL SFP XGSPON(1)", "SL TB XGSPON(2)", "Hiệu suất % = (2) / ((1) * 50)",
            "Hiệu suất % = (2) / ((1) * 40)"
          ]
      }
    }
  },

  "excel_qly_hsuat_xgspon_info": {
    "sheet_info": {
      "sheet_data": {
        "start_cell": "STT",
        "require_col": [
            "STT", "Mã tỉnh", "Địa điểm", "Loại", "Quận/Huyện", "Đơn vị", "Tên hệ thống",
            "IP", "Số lượng card XGSPON", "Vị trí card", "Tên Card", "SL Port",
            "SL SFP XGSPON(1)", "SL TB XGSPON(2)", "Hiệu suất % = (2) / ((1) * 50)",
            "Hiệu suất % = (2) / ((1) * 40)"
          ]
      }
    },
    "hint": "ex: Hiệu suất XGSPON(abc).xlsx | sheet: data(abc)"
  },

  "excel_rp_card_by_unit": {
    "sheet_info": {
      "sheet_data": {
        "start_cell": "Tên hệ thống",
        "require_col": [
            "Tên hệ thống", "Dòng", "Hãng sản xuất",
            "Slot", "Tên card", "Số Serial"
        ]
      }
    },
    "hint": "ex: ReportCardAccessByUnit(abc).xlsx | sheet: Sheet(abc)"
  },

  "excel_rp_trans_by_unit": {
    "sheet_info": {
      "sheet_data": {
        "start_cell": "Tên hệ thống",
        "require_col": ["Tên hệ thống", "Vị trí lắp", "Model P/N", "Số Serial"]
      }
    },
    "hint": "ex: ReportTransAccessByUnit(abc).xlsx | sheet: Sheet(abc)"
  },

  "excel_bc_chtiet_onu": {
    "sheet_info": {
      "sheet_data": {
        "start_cell": "System name",
        "require_col": [
          "Tỉnh/TP", "Đơn vị quản lý", "Tên nhà trạm", "System name",
          "Manager ip",
          "Frame no", "Slot no", "Port no", "Onu index",
          "Serial number",
          "Loại Onu", "Tên Onu", "Tên thuê bao",
        ]
      }
    },
    "hint": "ex: BaoCaoChiTietOnu(abc).xlsx | sheet: Sheet(abc)"
  },

  "excel_tghop_thbi_gpon_tren_mang": {
    "sheet_info": {
      "sheet_data": {
        "start_cell": "Tên hệ thống",
        "require_col": [
            "Tên hệ thống", "Địa chỉ IP", "Địa điểm", "Loại", "Số card ĐK",
            "LT4 (1)", "LT8 (2)", "LT16 (3)",
            "Cổng GE (6)", "Cổng 10GE (7)",
            "Sử dụng (9)", "Sử dụng (11)",
        ]
      }
    },
    "hint": "ex: tong hop thiet bi gpon tren mang(abc).xlsx | sheet: Sheet(abc)"
  },

  "excel_chtiet_thbao_fiber_xgspon": {
    "sheet_info": {
      "sheet_data": {
        "start_cell": "TRẠM",
        "require_col": [
          "TRẠM", "SYSTEM NAME", "SLOT", "PORT",
          "THUEBAO_ID", "CÔNG NGHỆ", "TRẠNG THÁI THUÊ BAO",
        ]
      }
    },
    "hint": "ex: (abc)BDH_187(abc).xlsx | sheet: Sheet(abc)"
  },

  "excel_thbi_access": {
    "sheet_info": {
      "sheet_data": {
        "start_cell": "Mã nhà trạm",
        "require_col": [
          "Mã nhà trạm", "Địa chỉ IP", "Tên hệ thống",
          "Dòng", "Chức năng"
        ]
      }
    },
    "hint": "ex: (abc)thiet bi access(abc).xlsx | sheet: Sheet(abc)"
  },

  "ds_tbao_xgspon_dong": {
    "sheet_info": {
      "sheet_data": {
        "start_cell": "Trạm",
        "require_col": [
          "Trạm", "Mã TB", "Tên TB", "Địa chỉ lắp đặt",
          "SYSTEM", "SLOT", "PORT",
          "VPI", "Công nghệ",
        ]
      }
    },
    "hint": "ex: (abc)BDH_189(abc).xlsx | sheet: Sheet(abc)"
  },

  "ds_tbao_xgspon_tay": {
    "sheet_info": {
      "sheet_data": {
        "start_cell": "MA_TB",
        "require_col": [
          "MA_TB", "TEN_TB", "DIACHI_LD", "CONGNGHE", "SYSTEM_NAME",
          "SLOT", "PORT",
        ]
      }
    },
    "hint": "ex: (abc)GLI_001(abc).xlsx | sheet: Sheet(abc)"
  },

  "tbao_fiber_visa_dong": {
    "sheet_info": {
      "sheet_data": {
        "start_cell": "Tài khoản dịch vụ",
        "require_col": [
            "Tài khoản dịch vụ", "Tên khách hàng", "Địa chỉ khách hàng",
            "Ngày nghiệm thu", "Tình trạng sử dụng", "BrasIP", "Tham số cổng",
            "Gói dịch vụ"
        ]
      }
    },
    "hint": "ex: (abc)BDH_Báo cáo danh sách tài khoản dịch vụ hiện có(abc).xlsx | sheet: Data(abc)"
  },

  "tbao_fiber_visa_tay": {
    "sheet_info": {
      "sheet_data": {
        "start_cell": "Tài khoản dịch vụ",
        "require_col": [
            "Tài khoản dịch vụ", "Tên khách hàng", "Địa chỉ khách hàng",
            "Ngày nghiệm thu", "Tình trạng sử dụng", "BrasIP", "Tham số cổng",
            "Gói dịch vụ"
        ]
      }
    },
    "hint": "ex: (abc)GLI_Báo cáo danh sách tài khoản dịch vụ hiện có(abc).xlsx | sheet: Data(abc)"
  },

  "megawan_metronet": {
    "sheet_info": {
      "sheet_data": {
        "start_cell": "id",
        "require_col": [
          "MÃ TB", "MÃ LT/MÃ TB SUB", "Tên thuê bao",
          "Địa chỉ lắp đặt", "id", "diemcuoi",
          "ipsource", "ipdes", "svlancvlan",
          "capadsl", "capodf", "ngaytacdong",
          "ghichu", "IP", "system", "portswitch",
          "UPE", "LOẠI HÌNH TB", "Trạng thái",
          "Tốc độ", "Đơn vị", "LOẠI KÊNH",
        ]
      }
    },
    "hint": "ex: (abc).xlsx | sheet: (abc)"
  },
}