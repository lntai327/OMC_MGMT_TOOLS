import inspect

from backend.util.ex_handle_util import ExcelHandleUtil
from share.util.dynamic_info_util import DynamicInfoUtil
from share.util.explorer_util import ExplorerUtil

from share.constant import constant as SC

class Cell4gSheet:
    def __init__(self):
        self.loai_doi_tuong = None
        self.ten_tren_he_thong = None
        self.ma_csht_cua_cell = None
        self.ma_csht_cua_tram = None
        self.dia_chi = None
        self.ten_quan_ly = None
        self.ten_don_vi = None
        self.trthai_hdong = None

    def __getitem__(self, key):
        if key == SC.K_LOAI_DOI_TUONG:
            return self.loai_doi_tuong
        elif key == SC.K_TEN_TREN_HE_THONG:
            return self.ten_tren_he_thong
        elif key == SC.K_MA_CSHT_CUA_CELL:
            return self.ma_csht_cua_cell
        elif key == SC.K_MA_CSHT_CUA_TRAM:
            return self.ma_csht_cua_tram
        elif key == SC.K_DIA_CHI:
            return self.dia_chi
        elif key == SC.K_TEN_QUAN_LY:
            return self.ten_quan_ly
        elif key == SC.K_TEN_DON_VI:
            return self.ten_don_vi
        elif key == SC.K_TRANG_THAI_HDONG:
            return self.trthai_hdong
        else:
            raise Exception(inspect.currentframe().f_code.co_name + "Invalid argument: " + key)

    def __repr__(self):
        return str(self.to_dict())

    def to_dict(self):
        return {
            SC.K_LOAI_DOI_TUONG: self.loai_doi_tuong,
            SC.K_TEN_TREN_HE_THONG: self.ten_tren_he_thong,
            SC.K_MA_CSHT_CUA_CELL: self.ma_csht_cua_cell, 
            SC.K_MA_CSHT_CUA_TRAM: self.ma_csht_cua_tram,
            SC.K_DIA_CHI: self.dia_chi,
            SC.K_TEN_QUAN_LY: self.ten_quan_ly,
            SC.K_TEN_DON_VI: self.ten_don_vi,
            SC.K_TRANG_THAI_HDONG: self.trthai_hdong
        }


    def load(self, cell4g_item_dic):
        self.loai_doi_tuong = cell4g_item_dic.get(SC.K_UI_LOAI_DOI_TUONG)
        self.ten_tren_he_thong = cell4g_item_dic.get(SC.K_UI_TEN_TREN_HE_THONG)
        self.ma_csht_cua_cell = cell4g_item_dic.get(SC.K_UI_MA_CSHT_CUA_CELL)
        self.ma_csht_cua_tram = cell4g_item_dic.get(SC.K_UI_MA_CSHT_CUA_TRAM)
        self.dia_chi = cell4g_item_dic.get(SC.K_UI_DIA_CHI)
        self.ten_quan_ly = cell4g_item_dic.get(SC.K_UI_TEN_QUAN_LY)
        self.ten_don_vi = cell4g_item_dic.get(SC.K_UI_TEN_DON_VI)
        self.trthai_hdong = cell4g_item_dic.get(SC.K_UI_TRANG_THAI_HDONG)
        return self

class ExcelCell4gLoader:
    def __init__(self):
        pass

    def load_cell4g_items(self):
        sheet_names = DynamicInfoUtil().get_value(
            4, SC.K_EXCEL_CELL4G_KEY, SC.K_REQUIRE_SHEET,
            SC.K_SHEET_CELL4G_KEY, SC.K_NAME
        )

        excel_path = ExplorerUtil().get_cache_file_path(
            DynamicInfoUtil().get_value(2, SC.K_EXCEL_CELL4G_KEY, SC.K_NAME)
        )

        all_items_in_sheet_list = []
        for sheet_name in sheet_names:
            items = ExcelHandleUtil().load_items(
                sheet_name=sheet_name,
                sheet_info_key=SC.K_SHEET_CELL4G_KEY,
                excel_info_key=SC.K_EXCEL_CELL4G_KEY,
                excel_path=excel_path
            )
            all_items_in_sheet_list.extend(items)

        return [Cell4gSheet().load(x) for x in all_items_in_sheet_list]