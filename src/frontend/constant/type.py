from enum import Enum, auto


class ReportTypeEnum(Enum):
    BC_CELL_MLL = auto()
    BC_BTS = auto()
    BC_MPD = auto()
    BC_CBAO_MLL = auto()
    QLY_HSUAT_XGSPON = auto()

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
        "Quản Lý Hiệu Suất XGSPON"
    )