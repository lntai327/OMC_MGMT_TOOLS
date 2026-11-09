import inspect

from backend.util.ex_handle_util import ExcelHandleUtil
from share.util.dynamic_info_util import DynamicInfoUtil
from share.util.explorer_util import ExplorerUtil
from share.util.logger_util import LoggerUtil

from share.constant import constant as SC

class DataSheet:
    def __init__(self):
        self._ten_ne = None
        self._object = None
        self._nnhan = None
        self._tgian_su_co = None
        self._tgian_clr = None
        self._tgain_cbao = None
        self._trthai_clr = None
        self._vnp_ghi_chu = None
        self._tinh_ghi_chu = None
        self._loai_su_co = None
        self._phan_loai_tram = None
        self._time_ac = None
        self._he_thong = None
        self._dvi_qly = None

    def __repr__(self):
        return str(self.to_dict())

    def to_dict(self):
        return {
            SC.K_TEN_NE: self._ten_ne,
            SC.K_OBJECT: self._object,
            SC.K_NGUYEN_NHAN: self._nnhan,
            SC.K_TG_SU_CO_1: self._tgian_su_co,
            SC.K_TG_CLR: self._tgian_clr,
            SC.K_TG_CBAO: self._tgain_cbao,
            SC.K_TTHAI_CLR: self._trthai_clr,
            SC.K_VNP_GHI_CHU: self._vnp_ghi_chu,
            SC.K_TINH_GHI_CHU: self._tinh_ghi_chu,
            SC.K_LOAI_SU_CO: self._loai_su_co,
            SC.K_PHAN_LOAI_TRAM: self._phan_loai_tram,
            SC.K_TIME_AC: self._time_ac,
            SC.K_HE_THONG: self._he_thong,
            SC.K_DVI_QLY: self._dvi_qly,
        }

    def load(self, item_dic):
        self._ten_ne = item_dic.get(SC.K_UI_TEN_NE)
        self._object = item_dic.get(SC.K_UI_OBJECT)
        self._nnhan = item_dic.get(SC.K_UI_NGUYEN_NHAN1)
        self._tgian_su_co = item_dic.get(SC.K_UI_TG_SU_CO1)
        self._tgian_clr = item_dic.get(SC.K_UI_TG_CLR)
        self._tgain_cbao = item_dic.get(SC.K_UI_TG_CBAO)
        self._trthai_clr = item_dic.get(SC.K_UI_TTHAI_CLR)
        self._vnp_ghi_chu = item_dic.get(SC.K_UI_VNP_GHI_CHU)
        self._tinh_ghi_chu = item_dic.get(SC.K_UI_TINH_GHI_CHU)
        self._loai_su_co = item_dic.get(SC.K_UI_LOAI_SU_CO)
        self._phan_loai_tram = item_dic.get(SC.K_UI_PHAN_LOAI_TRAM1)
        self._time_ac = item_dic.get(SC.K_UI_TIME_AC)
        self._he_thong = item_dic.get(SC.K_UI_HE_THONG)
        self._dvi_qly = item_dic.get(SC.K_UI_DON_VI_QUAN_LY)
        return self

class ExcelRpAlarmLoader:
    def __init__(self):
        pass

    def load_items(self):
        record_list: list[dict] = []
        sheet_names = DynamicInfoUtil().get_value(
            4, SC.K_EXCEL_RP_ALARM_KEY, SC.K_REQUIRE_SHEET,
            SC.K_SHEET_DATA, SC.K_NAME
        )

        for sheet_name in sheet_names:
            excel_path = ExplorerUtil().get_cache_file_path(
                DynamicInfoUtil().get_value(2, SC.K_EXCEL_RP_ALARM_KEY, SC.K_NAME)
            )
            ret_list = ExcelHandleUtil().load_items(
                sheet_name=sheet_name,
                sheet_info_key=SC.K_SHEET_DATA,
                excel_info_key=SC.K_EXCEL_RP_AL_BC_CBAO_MLL_KEY,
                excel_path=excel_path
            )
            record_list.extend(ret_list)

        return [DataSheet().load(x) for x in record_list]