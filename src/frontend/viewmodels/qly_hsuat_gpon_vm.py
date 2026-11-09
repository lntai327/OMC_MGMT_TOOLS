from collections import defaultdict
import math
import threading
import traceback
from typing import Callable, List, Optional

from backend.services.qly_hsuat_gpon_service import QlyHsuatGponService
from frontend.viewmodels.base_vm import BaseViewModel
from share.util.logger_util import LoggerUtil
from share.util.dynamic_info_util import DynamicInfoUtil
from share.constant import constant as SC
from share.constant import type as ST


class QlyHsuatGponViewModel(BaseViewModel):
    """
    ViewModel for the QlyHsuatXgsponInfoMd page.

    Observable keys:
        "is_loading"     — bool
        "data_changed"   — list / page updated
        "status_changed" — success/error messages updated
    """

    def __init__(self, service: Optional[QlyHsuatGponService] = None) -> None:
        super().__init__()
        self.page_size: int = 20        # Default 20 for table
        self.current_page: int = 1

        self._service = service or QlyHsuatGponService()

        self._hs_pon_record_dict_by_ten_hthong = defaultdict(list)
        self._tghop_record: List[dict] = []

        self._filter_field: str = SC.K_TEN_HE_THONG  # default filter field
        self._filter_value: str = ""
        self._error_message: str = ""
        self._success_message: str = ""
        self._path_message: str = ""
        self._is_loading: bool = False
        self._site: str = DynamicInfoUtil().get_value(2, SC.K_SCREEN_INPUT, SC.K_SITE1) or ST.Site.ALL_SITE.value
        self._slg_tbao_fsp: str = DynamicInfoUtil().get_value(2, SC.K_SCREEN_INPUT, "slg_tbao_fsp") or "40"
        self._gtri_hs_cbao: str = DynamicInfoUtil().get_value(2, SC.K_SCREEN_INPUT, "gtri_hs_sfp_cbao") or "100"

        self._data_lock: threading.Lock = threading.Lock()

    def set_on_change(self, callback: Callable) -> None:
        """Register generic callback for backwards compatibility."""
        self.subscribe("data_changed", callback)
        self.subscribe("status_changed", callback)
        self.subscribe("is_loading", callback)

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def is_loading(self) -> bool:
        return self._is_loading

    @is_loading.setter
    def is_loading(self, val: bool) -> None:
        self._is_loading = val
        self.notify("is_loading")

    @property
    def error_message(self) -> str:
        return self._error_message

    @error_message.setter
    def error_message(self, msg: str) -> None:
        self._error_message = msg
        self.notify("status_changed")

    @property
    def success_message(self) -> str:
        return self._success_message

    @success_message.setter
    def success_message(self, msg: str) -> None:
        self._success_message = msg
        self.notify("status_changed")

    @property
    def path_message(self) -> str:
        return self._path_message

    @path_message.setter
    def path_message(self, msg: str) -> None:
        self._path_message = msg
        self.notify("status_changed")

    @property
    def slg_tbao_fsp(self) -> str:
        return self._slg_tbao_fsp

    @slg_tbao_fsp.setter
    def slg_tbao_fsp(self, v: str):
        self._slg_tbao_fsp = v
        DynamicInfoUtil().set_value(v, 2, SC.K_SCREEN_INPUT, "slg_tbao_fsp")

    @property
    def site(self) -> str:
        return self._site

    @site.setter
    def site(self, v: str):
        self._site = v
        DynamicInfoUtil().set_value(v, 2, SC.K_SCREEN_INPUT, SC.K_SITE1)

    # ------------------------------------------------------------------
    # Filtering & Pagination
    # ------------------------------------------------------------------

    # Mapping from filter_field to the dict key used in records
    FILTER_FIELD_MAP = {
        SC.K_TEN_HE_THONG: SC.K_TEN_HE_THONG,
        SC.K_IP: SC.K_IP,
        SC.K_TTVT: SC.K_TTVT,
        SC.K_PHUONG_XA: SC.K_PHUONG_XA,
    }

    @property
    def filtered_record(self) -> List[dict]:
        """Return record matching current filter field & value."""
        result = self._tghop_record

        if self._filter_value.strip():
            q = self._filter_value.strip().lower()
            key = self.FILTER_FIELD_MAP.get(self._filter_field)
            if key:
                result = [
                    e for e in result
                    if e.get(key, "") and q in e.get(key, "").lower()
                ]

        counter = 1
        for item in result:
            item[SC.K_STT] = counter
            counter += 1

        return result

    @property
    def total_pages(self) -> int:
        total = len(self.filtered_record)
        if total == 0:
            return 1
        return math.ceil(total / self.page_size)

    @property
    def paginated_record(self) -> List[dict]:
        filtered = self.filtered_record
        if self.current_page > self.total_pages:
            self.current_page = max(1, self.total_pages)
        start = (self.current_page - 1) * self.page_size
        end = start + self.page_size
        return filtered[start:end]
    
    @property
    def gtri_hs_cbao(self) -> str:
        return self._gtri_hs_cbao

    @gtri_hs_cbao.setter
    def gtri_hs_cbao(self, v: str):
        self._gtri_hs_cbao = v
        DynamicInfoUtil().set_value(v, 2, SC.K_SCREEN_INPUT, "gtri_hs_sfp_cbao")

    def set_page_size(self, size: int) -> None:
        if size in (10, 20, 50, 100):
            self.page_size = size
            self.current_page = 1
            self.notify("data_changed")

    def go_to_page(self, page_num: int) -> None:
        if 1 <= page_num <= self.total_pages:
            self.current_page = page_num
            self.notify("data_changed")

    def set_filter(self, field: str, value: str) -> None:
        """Set the active filter field and value, then refresh."""
        self._filter_field = field
        self._filter_value = value
        self.current_page = 1
        self.notify("data_changed")

    # ------------------------------------------------------------------
    # Data Operations
    # ------------------------------------------------------------------

    def load(self) -> None:
        """Load all records from the service"""
        self.is_loading = True
        try:
            with self._data_lock:
                hs_pon_record, self._tghop_record = self._service.get_preview()

                self._hs_pon_record_dict_by_ten_hthong.clear()
                for record in hs_pon_record:
                    ten_hthong = record.get(SC.K_TEN_HE_THONG)
                    if ten_hthong:
                        record[SC.K_STT] = len(self._hs_pon_record_dict_by_ten_hthong[ten_hthong]) + 1
                        self._hs_pon_record_dict_by_ten_hthong[ten_hthong].append(record)
            
            self._error_message = ""
        except Exception as exc:
            tb = traceback.format_exc()
            LoggerUtil.get_logger().error(f"QlyHsuatGponViewModel load error: {exc}, traceback: {tb}")
            self._error_message = f"Failed to load data"
            self._hs_pon_record_dict_by_ten_hthong.clear()
            self._tghop_record = []
        finally:
            self.is_loading = False
            self.notify("data_changed")

    def get_detail_records_by_ten_hthong(self, ten_he_thong: str) -> list[dict]:
        with self._data_lock:
            records = self._hs_pon_record_dict_by_ten_hthong.get(ten_he_thong)
            if records is None:
                target_key = str(ten_he_thong).strip().lower()
                for k, v in self._hs_pon_record_dict_by_ten_hthong.items():
                    if str(k).strip().lower() == target_key:
                        return list(v)
                return []
            return list(records)

    def load_in_background(self, page) -> None:
        if self._is_loading:
            return
        page.run_thread(self.load)

    def export_to_excel(self, folder_path: str) -> None:
        """Export EXACTLY the filtered/searched record list to Excel."""
        self.is_loading = True
        self._success_message = ""
        self._error_message = ""
        self._path_message = ""
        self.notify("status_changed")

        try:
            _filtered_record = self.filtered_record
            with self._data_lock:
                ret_path = self._service.export_to_excel(
                    _filtered_record, folder_path
                )
            actual_path = ret_path or folder_path
            self._success_message = \
                f"Xuất bản ghi thành công → {actual_path}"
            self._path_message = f"{actual_path}"
            self._error_message = ""
        except Exception as exc:
            tb = traceback.format_exc()
            LoggerUtil.get_logger().error(f"QlyHsuatGponViewModel export error: {exc}, traceback: {tb}")
            self._error_message = f"Export failed"
            self._success_message = ""
            self._path_message = ""
        finally:
            self.is_loading = False
            self.notify("status_changed")

    def get_db_update_list(self) -> list[str]:
        return [
            SC.K_EXCEL_CSHT_CCL_KEY,
            SC.K_EXCEL_RP_CARD_BY_UNIT,
            SC.K_EXCEL_RP_TRANS_BY_UNIT,
            SC.K_EXCEL_THBI_ACCESS,
            SC.K_EXCEL_BC_CHTIET_ONU,
            SC.K_EXCEL_TBAO_FIBER_VISA_DONG,
            SC.K_EXCEL_TBAO_FIBER_VISA_TAY,
            SC.K_EXCEL_DS_THBAO_XGSPON_DONG,
            SC.K_EXCEL_DS_THBAO_XGSPON_TAY,
        ]