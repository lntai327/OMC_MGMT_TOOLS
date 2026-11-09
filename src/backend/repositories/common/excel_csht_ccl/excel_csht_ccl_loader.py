import inspect

from backend.util.excel_loader_util import ExcelLoaderUtil
from share.util.dynamic_info_util import DynamicInfoUtil
from share.util.explorer_util import ExplorerUtil
from share.constant import constant as SC

class CshtMdsdSheet:
    def __init__(self):
        self._ma_csht = None
        self._ten_csht = None
        self._ten_dvi_qly = None
        self._trang_thai = None
        self._ten_ttvt_tram_vtnetx = None
        self._loai_nha_tram = None
        self._phuong_xa = None
        self._dia_chi = None
        self._trthai_dat_mno = None
        self._ma_loai_csht_ddong = None

    def __getitem__(self, key):
        match key:
            case SC.K_MA_CSHT:
                return self._ma_csht
            case SC.K_TEN_CSHT:
                return self._ten_csht
            case SC.K_TEN_DVI_QLY: #Tổ hạ tầng
                return self._ten_dvi_qly
            case SC.K_TRANG_THAI:
                return self._trang_thai
            case SC.K_TEN_TTVT_TRAM_VT_NETX:
                return self._ten_ttvt_tram_vtnetx
            case SC.K_LOAI_NHA_TRAM:
                return self._loai_nha_tram
            case SC.K_PHUONG_XA:
                return self._phuong_xa
            case SC.K_DIA_CHI:
                return self._dia_chi
            case SC.K_TRTHAI_DAT_MNO:
                return self._trthai_dat_mno
            case SC.K_MA_LOAI_CSHT_DDONG:
                return self._ma_loai_csht_ddong
            case _:
                raise Exception(inspect.currentframe().f_code.co_name + "Invalid argument: " + key)

    def __repr__(self):
        return str(self.to_dict())

    def to_dict(self):
        return {
            SC.K_MA_CSHT: self._ma_csht,
            SC.K_TEN_CSHT: self._ten_csht,
            SC.K_TEN_DVI_QLY: self._ten_dvi_qly,
            SC.K_TRANG_THAI: self._trang_thai,
            SC.K_TEN_TTVT_TRAM_VT_NETX: self._ten_ttvt_tram_vtnetx,
            SC.K_LOAI_NHA_TRAM: self._loai_nha_tram,
            SC.K_PHUONG_XA: self._phuong_xa,
            SC.K_DIA_CHI: self._dia_chi,
            SC.K_TRTHAI_DAT_MNO: self._trthai_dat_mno,
            SC.K_MA_LOAI_CSHT_DDONG: self._ma_loai_csht_ddong
        }

    def load(self, item_dic):
        self._ma_csht = item_dic.get(SC.K_UI_MA_CSHT)
        self._ten_csht = item_dic.get(SC.K_UI_TEN_CSHT)
        self._ten_dvi_qly = item_dic.get(SC.K_UI_TEN_DVI_QLY)
        self._trang_thai = item_dic.get(SC.K_UI_TRANG_THAI)
        self._ten_ttvt_tram_vtnetx = item_dic.get(SC.K_UI_TEN_TTVT_TRAM_VT_NETX)
        self._loai_nha_tram = item_dic.get(SC.K_UI_LOAI_NHA_TRAM)
        self._phuong_xa = item_dic.get(SC.K_UI_PHUONG_XA)
        self._dia_chi = item_dic.get(SC.K_UI_DIA_CHI)
        self._trthai_dat_mno = item_dic.get(SC.K_UI_TRTHAI_DAT_MNO)
        self._ma_loai_csht_ddong = item_dic.get(SC.K_UI_MA_LOAI_CSHT_DI_DONG)

        return self

class ExcelCshtCclLoader:
    def __init__(self):
        pass

    def load_items(self):
        sheet_name = DynamicInfoUtil().get_value(
            4, SC.K_EXCEL_CSHT_CCL_KEY, SC.K_REQUIRE_SHEET,
            SC.K_SHEET_CSHT_MDSDL_KEY, SC.K_NAME
        )
        excel_path = ExplorerUtil().get_cache_file_path(
            DynamicInfoUtil().get_value(2, SC.K_EXCEL_CSHT_CCL_KEY, SC.K_NAME)
        )
        all_items_in_sheet_list = ExcelLoaderUtil().load_items(
            sheet_name=sheet_name,
            sheet_info_key=SC.K_SHEET_CSHT_MDSDL_KEY,
            excel_info_key=SC.K_EXCEL_CSHT_CCL_KEY,
            excel_path=excel_path
        )
        return [CshtMdsdSheet().load(x) for x in all_items_in_sheet_list]