import inspect

from backend.util.ex_handle_util import ExcelHandleUtil
from share.util.dynamic_info_util import DynamicInfoUtil
from share.util.explorer_util import ExplorerUtil

from share.constant import constant as SC

class Cell5gSheet:
    def __init__(self):
        self.loai_doi_tuong = None
        self.ten_tren_he_thong = None
        self.ma_csht = None #cell
        # self.ma_csht_cua_tram = None
        self.dia_chi = None
        self.ten_quan_ly = None
        self.trthai_hdong = None
        self.ten_don_vi = None

    def __getitem__(self, key):
        if key == SC.K_LOAI_DOI_TUONG:
            return self.loai_doi_tuong
        elif key == SC.K_TEN_TREN_HE_THONG:
            return self.ten_tren_he_thong
        elif key == SC.K_MA_CSHT:
            return self.ma_csht
        elif key == SC.K_DIA_CHI:
            return self.dia_chi
        elif key == SC.K_TEN_QUAN_LY:
            return self.ten_quan_ly
        elif key == SC.K_TRANG_THAI_HDONG:
            return self.trthai_hdong
        elif key == SC.K_TEN_DON_VI:
            return self.ten_don_vi
        else:
            raise Exception(inspect.currentframe().f_code.co_name + "Invalid argument: " + key)

    def __repr__(self):
        return str(self.to_dict())

    def to_dict(self):
        return {
            SC.K_LOAI_DOI_TUONG: self.loai_doi_tuong,
            SC.K_TEN_TREN_HE_THONG: self.ten_tren_he_thong,
            SC.K_MA_CSHT: self.ma_csht, 
            SC.K_DIA_CHI: self.dia_chi,
            SC.K_TEN_QUAN_LY: self.ten_quan_ly,
            SC.K_TRANG_THAI_HDONG: self.trthai_hdong,
            SC.K_TEN_DON_VI: self.ten_don_vi
        }


    def load(self, item_dic):
        self.loai_doi_tuong = item_dic.get(SC.K_UI_LOAI_DOI_TUONG)
        self.ten_tren_he_thong = item_dic.get(SC.K_UI_TEN_TREN_HE_THONG)
        self.ma_csht = item_dic.get(SC.K_UI_MA_CSHT)
        self.dia_chi = item_dic.get(SC.K_UI_DIA_CHI)
        self.ten_quan_ly = item_dic.get(SC.K_UI_TEN_QUAN_LY)
        self.trthai_hdong = item_dic.get(SC.K_UI_TRANG_THAI_HDONG)
        self.ten_don_vi = item_dic.get(SC.K_UI_TEN_DON_VI)
        return self

class ExcelCell5gLoader:
    def __init__(self):
        pass

    def load_items(self):
        sheet_names = DynamicInfoUtil().get_value(
            4, SC.K_EXCEL_CELL5G_KEY, SC.K_REQUIRE_SHEET,
            SC.K_SHEET_CELL5G_KEY, SC.K_NAME
        )

        excel_path = ExplorerUtil().get_cache_file_path(
            DynamicInfoUtil().get_value(2, SC.K_EXCEL_CELL5G_KEY, SC.K_NAME)
        )

        all_items_in_sheet_list = []
        for sheet_name in sheet_names:
            items = ExcelHandleUtil().load_items(
                sheet_name=sheet_name,
                sheet_info_key=SC.K_SHEET_CELL5G_KEY,
                excel_info_key=SC.K_EXCEL_CELL5G_KEY,
                excel_path=excel_path
            )
            all_items_in_sheet_list.extend(items)

        return [Cell5gSheet().load(x) for x in all_items_in_sheet_list]