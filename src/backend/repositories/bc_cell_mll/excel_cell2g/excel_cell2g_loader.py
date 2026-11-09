import inspect

from backend.util.excel_loader_util import ExcelLoaderUtil
from share.util.dynamic_info_util import DynamicInfoUtil
from share.util.explorer_util import ExplorerUtil

from share.constant import constant as SC

class Cell2gSheet:
    def __init__(self):
        self.ten_tren_he_thong = None
        self.ten_loai_ne = None
        self.ma_csht_cua_cell = None
        self.ma_csht_cua_tram = None
        self.dia_chi = None
        self.trthai_hdong = None
        self.ten_quan_ly = None
        self.ten_don_vi = None

    def __getitem__(self, key):
        if key == SC.K_TEN_TREN_HE_THONG:
            return self.ten_tren_he_thong
        elif key == SC.K_TEN_LOAI_NE:
            return self.ten_loai_ne
        elif key == SC.K_MA_CSHT_CUA_CELL:
            return self.ma_csht_cua_cell
        elif key == SC.K_MA_CSHT_CUA_TRAM:
            return self.ma_csht_cua_tram
        elif key == SC.K_DIA_CHI:
            return self.dia_chi
        elif key == SC.K_TRANG_THAI_HDONG:
            return self.trthai_hdong
        elif key == SC.K_TEN_QUAN_LY:
            return self.ten_quan_ly
        elif key == SC.K_TEN_DON_VI:
            return self.ten_don_vi
        else:
            raise Exception(inspect.currentframe().f_code.co_name + "Invalid argument: " + key)
        
    # def __setitem__(self, key, value):
    #     if key == SC.K_LOAI_DOI_TUONG:
    #         self.loai_doi_tuong = value
    #     else:
    #         raise Exception(inspect.currentframe().f_code.co_name + "Invalid argument: " + key)

    def __repr__(self):
        return str(self.to_dict())

    def to_dict(self):
        return {
            SC.K_TEN_TREN_HE_THONG: self.ten_tren_he_thong,
            SC.K_TEN_LOAI_NE: self.ten_loai_ne,
            SC.K_MA_CSHT_CUA_CELL: self.ma_csht_cua_cell, 
            SC.K_MA_CSHT_CUA_TRAM: self.ma_csht_cua_tram,
            SC.K_DIA_CHI: self.dia_chi,
            SC.K_TRANG_THAI_HDONG: self.trthai_hdong,
            SC.K_TEN_QUAN_LY: self.ten_quan_ly,
            SC.K_TEN_DON_VI: self.ten_don_vi
        }


    def load(self, cell2g_item_dic):
        self.ten_tren_he_thong = cell2g_item_dic.get(SC.K_UI_TEN_TREN_HE_THONG)
        self.ten_loai_ne = cell2g_item_dic.get(SC.K_UI_TEN_LOAI_NE)
        self.ma_csht_cua_cell = cell2g_item_dic.get(SC.K_UI_MA_CSHT_CUA_CELL)
        self.ma_csht_cua_tram = cell2g_item_dic.get(SC.K_UI_MA_CSHT_CUA_TRAM)
        self.dia_chi = cell2g_item_dic.get(SC.K_UI_DIA_CHI)
        self.trthai_hdong = cell2g_item_dic.get(SC.K_UI_TRANG_THAI_HDONG)
        self.ten_quan_ly = cell2g_item_dic.get(SC.K_UI_TEN_QUAN_LY)
        self.ten_don_vi = cell2g_item_dic.get(SC.K_UI_TEN_DON_VI)
        return self

class ExcelCell2gLoader:
    def __init__(self):
        pass

    def load_cell2g_items(self):
        sheet_name = DynamicInfoUtil().get_value(
            4, SC.K_EXCEL_CELL2G_KEY, SC.K_REQUIRE_SHEET,
            SC.K_SHEET_CELL2G_KEY, SC.K_NAME
        )
        excel_path = ExplorerUtil().get_cache_file_path(
            DynamicInfoUtil().get_value(2, SC.K_EXCEL_CELL2G_KEY, SC.K_NAME)
        )
        all_items_in_sheet_list = ExcelLoaderUtil().load_items(
            sheet_name=sheet_name,
            sheet_info_key=SC.K_SHEET_CELL2G_KEY,
            excel_info_key=SC.K_EXCEL_CELL2G_KEY,
            excel_path=excel_path
        )
        return [Cell2gSheet().load(x) for x in all_items_in_sheet_list]