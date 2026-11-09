from share.util import explorer_util
from frontend.component import explorer_ui_util
import inspect

from backend.util.excel_loader_util import ExcelLoaderUtil
from share.util.dynamic_info_util import DynamicInfoUtil
from share.util.explorer_util import ExplorerUtil

from share.constant import constant as SC

class Cell3gSheet:
    def __init__(self):
        self.trthai_hdong = None
        self.ten_tren_he_thong = None
        self.ma_csht_cua_cell = None
        self.ma_csht_cua_tram = None
        self.loai_doi_tuong = None
        self.dia_chi = None
        self.ten_quan_ly = None
        self.ten_don_vi = None

    def __getitem__(self, key):
        if key == SC.K_TRANG_THAI_HDONG:
            return self.trthai_hdong
        elif key == SC.K_TEN_TREN_HE_THONG:
            return self.ten_tren_he_thong
        elif key == SC.K_MA_CSHT_CUA_CELL:
            return self.ma_csht_cua_cell
        elif key == SC.K_MA_CSHT_CUA_TRAM:
            return self.ma_csht_cua_tram
        elif key == SC.K_LOAI_DOI_TUONG:
            return self.loai_doi_tuong
        elif key == SC.K_DIA_CHI:
            return self.dia_chi
        elif key == SC.K_TEN_QUAN_LY:
            return self.ten_quan_ly
        elif key == SC.K_TEN_DON_VI:
            return self.ten_don_vi
        else:
            raise Exception(inspect.currentframe().f_code.co_name + "Invalid argument: " + key)

    def __repr__(self):
        return str(self.to_dict())

    def to_dict(self):
        return {
            SC.K_TRANG_THAI_HDONG: self.trthai_hdong,
            SC.K_TEN_TREN_HE_THONG: self.ten_tren_he_thong,
            SC.K_MA_CSHT_CUA_CELL: self.ma_csht_cua_cell, 
            SC.K_MA_CSHT_CUA_TRAM: self.ma_csht_cua_tram,
            SC.K_LOAI_DOI_TUONG: self.loai_doi_tuong,
            SC.K_DIA_CHI: self.dia_chi,
            SC.K_TEN_QUAN_LY: self.ten_quan_ly,
            SC.K_TEN_DON_VI: self.ten_don_vi
        }


    def load(self, cell3g_item_dic):
        self.trthai_hdong = cell3g_item_dic.get(SC.K_UI_TRANG_THAI_HDONG)
        self.ten_tren_he_thong = cell3g_item_dic.get(SC.K_UI_TEN_TREN_HE_THONG)
        self.ma_csht_cua_cell = cell3g_item_dic.get(SC.K_UI_MA_CSHT_CUA_CELL)
        self.ma_csht_cua_tram = cell3g_item_dic.get(SC.K_UI_MA_CSHT_CUA_TRAM)
        self.loai_doi_tuong = cell3g_item_dic.get(SC.K_UI_LOAI_DOI_TUONG)
        self.dia_chi = cell3g_item_dic.get(SC.K_UI_DIA_CHI)
        self.ten_quan_ly = cell3g_item_dic.get(SC.K_UI_TEN_QUAN_LY)
        self.ten_don_vi = cell3g_item_dic.get(SC.K_UI_TEN_DON_VI)
        return self

class ExcelCell3gLoader:
    def __init__(self):
        pass

    def load_cell3g_items(self):
        sheet_name = DynamicInfoUtil().get_value(
            4, SC.K_EXCEL_CELL3G_KEY, SC.K_REQUIRE_SHEET,
            SC.K_SHEET_CELL3G_KEY, SC.K_NAME
        )
        excel_path = ExplorerUtil().get_cache_file_path(
            DynamicInfoUtil().get_value(2, SC.K_EXCEL_CELL3G_KEY, SC.K_NAME)
        )
        all_items_in_sheet_list = ExcelLoaderUtil().load_items(
            sheet_name=sheet_name,
            sheet_info_key=SC.K_SHEET_CELL3G_KEY,
            excel_info_key=SC.K_EXCEL_CELL3G_KEY,
            excel_path=excel_path
        )
        return [Cell3gSheet().load(x) for x in all_items_in_sheet_list]