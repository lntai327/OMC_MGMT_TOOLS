from enum import Enum, auto

class ReportTypeEnum(Enum):
    BC_CELL_MLL = auto()
    BC_BTS = auto()
    BC_MPD = auto()
    BC_CBAO_MLL = auto()
    QLY_HSUAT_XGSPON = auto()
    QLY_MEGAWAN = auto()

class ReportInfoStruct:
    def __init__(self, report_id, report_name):
        self.report_id = report_id
        self.report_name = report_name

class ReportTypeInfo:
    BC_CELL_MLL = ReportInfoStruct(
        ReportTypeEnum.BC_CELL_MLL,
        "Báo Cáo Cell Mất Liên Lạc"
    )
    BC_BTS = ReportInfoStruct(
        ReportTypeEnum.BC_BTS,
        "Báo Cáo BTS"
    )
    BC_MPD = ReportInfoStruct(
        ReportTypeEnum.BC_MPD,
        "MPD"
    )
    BC_CBAO_MLL = ReportInfoStruct(
        ReportTypeEnum.BC_CBAO_MLL,
        "CBAO MLL"
    )
    QLY_HSUAT_XGSPON = ReportInfoStruct(
        ReportTypeEnum.QLY_HSUAT_XGSPON,
        "Quản Lý Hiệu Suất Mạng GPON VNPT GLI"
    )
    QLY_MEGAWAN = ReportInfoStruct(
        ReportTypeEnum.QLY_MEGAWAN,
        "Quản Lý Megawan - Metronet VNPT GLI"
    )

######################################################################

class FileEnum(Enum):
    excel_csht_ccl = auto()
    excel_rp_card_by_unit = auto()
    excel_rp_trans_by_unit = auto()
    excel_thbi_access = auto()
    excel_bc_chtiet_onu = auto()
    tbao_fiber_visa_dong = auto()
    tbao_fiber_visa_tay = auto()
    ds_tbao_xgspon_dong = auto()
    ds_tbao_xgspon_tay = auto()
    megawan_metronet = auto()

class FileInfoStruct:
    def __init__(self, file_id, file_name):
        self.file_id = file_id
        self.file_name = file_name

FileInfoDict: dict = {
    FileEnum.excel_csht_ccl.name: FileInfoStruct(
        FileEnum.excel_csht_ccl,
        "CSHT"
    ),
    FileEnum.excel_rp_card_by_unit.name: FileInfoStruct(
        FileEnum.excel_rp_card_by_unit,
        "Card OLT"
    ),
    FileEnum.excel_rp_trans_by_unit.name: FileInfoStruct(
        FileEnum.excel_rp_trans_by_unit,
        "SFP port OLT"
    ),
    FileEnum.excel_thbi_access.name: FileInfoStruct(
        FileEnum.excel_thbi_access,
        "Thiết bị OLT"
    ),
    FileEnum.excel_bc_chtiet_onu.name: FileInfoStruct(
        FileEnum.excel_bc_chtiet_onu,
        "Chi tiết ONU theo RIMS"
    ),
    FileEnum.tbao_fiber_visa_dong.name: FileInfoStruct(
        FileEnum.tbao_fiber_visa_dong,
        "Thuê bao Fiber theo VISA (Đông)"
    ),
    FileEnum.tbao_fiber_visa_tay.name: FileInfoStruct(
        FileEnum.tbao_fiber_visa_tay,
        "Thuê bao Fiber theo VISA (Tây)"
    ),
    FileEnum.ds_tbao_xgspon_dong.name: FileInfoStruct(
        FileEnum.ds_tbao_xgspon_dong,
        "DS thuê bao XGSPON (Đông)"
    ),
    FileEnum.ds_tbao_xgspon_tay.name: FileInfoStruct(
        FileEnum.ds_tbao_xgspon_tay,
        "DS thuê bao XGSPON (Tây)"
    ),
    FileEnum.megawan_metronet.name: FileInfoStruct(
        FileEnum.megawan_metronet,
        "Megawan - Metronet"
    ),
}
