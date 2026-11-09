from backend.util.database_util import DatabaseFactory
from backend.util.ex_handle_util import ExcelHandleUtil
from share.util.dynamic_info_util import DynamicInfoUtil
from share.util.explorer_util import ExplorerUtil
from share.constant import constant as SC

class Nodeb3gSheet:
    def __init__(self):
        self._trang_thai_hdong = None
        self._ma_csht = None
        self._ten_tren_he_thong = None
        self._ten_quan_ly = None
        self._trthai_dat_mno = None
        self._loai_tram = None
        self._bg_tan = None
        self._ngay_duyet = None
        self._service_ip = None
        self._oam_ip = None

    def __repr__(self):
        return str(self.to_dict())

    def to_dict(self):
        return {
            SC.K_TRANG_THAI_HDONG: self._trang_thai_hdong,
            SC.K_MA_CSHT: self._ma_csht,
            SC.K_TEN_TREN_HE_THONG: self._ten_tren_he_thong,
            SC.K_TEN_QUAN_LY: self._ten_quan_ly,
            SC.K_TRTHAI_DAT_MNO: self._trthai_dat_mno,
            SC.K_LOAI_TRAM: self._loai_tram,
            SC.K_BG_TAN: self._bg_tan,
            SC.K_NGAY_DUYET: self._ngay_duyet,
            SC.K_SERVICE_IP: self._service_ip,
            SC.K_OAM_IP: self._oam_ip,
        }

    def load(self, item_dic):
        self._trang_thai_hdong = item_dic.get(SC.K_UI_TRANG_THAI_HDONG)
        self._ma_csht = item_dic.get(SC.K_UI_MA_CSHT)
        self._ten_tren_he_thong = item_dic.get(SC.K_UI_TEN_TREN_HE_THONG)
        self._ten_quan_ly = item_dic.get(SC.K_UI_TEN_QUAN_LY)
        self._trthai_dat_mno = item_dic.get(SC.K_UI_TRTHAI_DAT_MNO)
        self._loai_tram = item_dic.get(SC.K_UI_LOAI_TRAM)
        self._bg_tan = item_dic.get("Băng tần")
        self._ngay_duyet = item_dic.get("Ngày kiểm duyệt")
        self._service_ip = item_dic.get("Service IP")
        self._oam_ip = item_dic.get("OAM IP")

        return self

class ExcelNodeb3gLoader:
    def __init__(self):
        pass

    def load_items(self):
        sheet_names = DynamicInfoUtil().get_value(
            4, SC.K_EXCEL_NODEB3G_KEY, SC.K_REQUIRE_SHEET,
            SC.K_SHEET_NODEB3G_KEY, SC.K_NAME
        )

        excel_path = ExplorerUtil().get_cache_file_path(
            DynamicInfoUtil().get_value(2, SC.K_EXCEL_NODEB3G_KEY, SC.K_NAME)
        )

        all_items_in_sheet_list = []
        for sheet_name in sheet_names:
            items = ExcelHandleUtil().load_items(
                sheet_name=sheet_name,
                sheet_info_key=SC.K_SHEET_NODEB3G_KEY,
                excel_info_key=SC.K_EXCEL_NODEB3G_KEY,
                excel_path=excel_path
            )
            all_items_in_sheet_list.extend(items)

        return [Nodeb3gSheet().load(x) for x in all_items_in_sheet_list]

class ExcelNodeb3gService():
    def __init__(self):
        self._db_adapter = DatabaseFactory.create_adapter()
        self.nodeb3g_items_list_all = []

    def load(self):
        self._load_items_list_from_db()
        self._normalize()

    def _normalize(self):
        pass

    def update_db(self):
        self._loadFromExcel()
        self._write_to_db()

    def _loadFromExcel(self):
        # load items
        items_list_latest_all = ExcelNodeb3gLoader().load_items()
        items_list_latest_all = [item.to_dict() for item in items_list_latest_all]
        self.nodeb3g_items_list_all = list(
            item for item in items_list_latest_all \
            if str(item[SC.K_TRANG_THAI_HDONG]).lower() == "onair" #nomalize data
        )

    def _write_to_db(self):
        self._db_adapter.write_to_db(SC.K_TABLE_NODEB3G, self.nodeb3g_items_list_all)

    def _load_items_list_from_db(self):
        loaded_items = self._db_adapter.load(SC.K_TABLE_NODEB3G)
        for item in loaded_items:
            ten_hthong = str(item[SC.K_TEN_TREN_HE_THONG])

            item[SC.K_TEN_TREN_HE_THONG_COMPACT] = (
                ten_hthong[2:].replace("-", "")
                if ten_hthong
                else ""
            )

        self.nodeb3g_items_list_all = list(loaded_items) if loaded_items else []