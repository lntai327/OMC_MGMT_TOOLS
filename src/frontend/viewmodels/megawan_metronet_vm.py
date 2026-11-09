import math
import threading
import traceback
from typing import Callable, Dict, List, Optional

from backend.services.megawan_metronet_service import MegawanMetronetService
from frontend.viewmodels.base_vm import BaseViewModel
from share.constant import constant as SC
from share.util.logger_util import LoggerUtil


class MegawanMetronetViewModel(BaseViewModel):
    """
    ViewModel for the Megawan management page.

    Observable keys:
        "is_loading"              — bool
        "data_changed"            — table data / page updated
        "status_changed"          — success/error messages updated
        "selected_record_changed" — single selected record updated
    """

    EXACT_SEARCH_FIELDS = [
        SC.K_LOAI_HINH_TB,
        SC.K_TEN_TH_BAO,
        SC.K_DIA_CHI,
        SC.K_LOAI_KENH,
        SC.K_SVLAN_CVLAN,
        SC.K_TEN_HE_THONG,
    ]

    ALL_KEY = "ALL"

    def __init__(self, service: Optional[MegawanMetronetService] = None) -> None:
        super().__init__()
        self._service = service or MegawanMetronetService()

        self.page_size: int = 20
        self.current_page: int = 1

        self._all_records: List[dict] = []
        self._selected_record: Optional[dict] = None

        self._filters: Dict[str, str] = {
            SC.K_LOAI_HINH_TB: "",
            SC.K_TEN_TH_BAO: "",
            SC.K_DIA_CHI: "",
            SC.K_LOAI_KENH: "",
            SC.K_SVLAN_CVLAN: "",
            SC.K_TEN_HE_THONG: "",
            self.ALL_KEY: "",
        }

        self._is_loading: bool = False
        self._error_message: str = ""
        self._success_message: str = ""
        self._path_message: str = ""

        self._data_lock = threading.Lock()

    # ------------------------------------------------------------------
    # Observables & Properties
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
    def selected_record(self) -> Optional[dict]:
        return self._selected_record

    def set_selected_record(self, record: Optional[dict]) -> None:
        self._selected_record = record
        self.notify("selected_record_changed")

    # ------------------------------------------------------------------
    # Filtering & Pagination
    # ------------------------------------------------------------------

    @property
    def filters(self) -> Dict[str, str]:
        return dict(self._filters)

    def apply_filters(self, filter_dict: Dict[str, str]) -> None:
        """Apply new search filter values and reset to page 1."""
        for k in self._filters.keys():
            if k in filter_dict:
                self._filters[k] = filter_dict[k].strip()
        self.current_page = 1
        self.notify("data_changed")

    def reset_filters(self) -> None:
        """Clear all search filter values."""
        for k in self._filters.keys():
            self._filters[k] = ""
        self.current_page = 1
        self.notify("data_changed")

    @property
    def filtered_records(self) -> List[dict]:
        """Return records matching both column-exact filters and the ALL filter."""
        with self._data_lock:
            result = list(self._all_records)

        # Check column-exact filters
        for col in self.EXACT_SEARCH_FIELDS:
            target = self._filters.get(col, "").strip()
            if target:
                target_lower = target.lower()
                result = [
                    r for r in result
                    if target_lower in str(r.get(col, "")).strip().lower()
                ]

        # Check ALL filter (substring across all data fields)
        all_kw = self._filters.get(self.ALL_KEY, "").strip()
        if all_kw:
            kw_lower = all_kw.lower()
            fields = MegawanMetronetService.DATA_FIELDS
            result = [
                r for r in result
                if any(kw_lower in str(r.get(f, "")).lower() for f in fields)
            ]

        # Add 1-based STT for display
        for idx, item in enumerate(result, 1):
            item[SC.K_STT] = idx

        return result

    @property
    def total_records_count(self) -> int:
        return len(self.filtered_records)

    @property
    def total_pages(self) -> int:
        count = self.total_records_count
        return max(1, math.ceil(count / self.page_size))

    @property
    def paginated_records(self) -> List[dict]:
        filtered = self.filtered_records
        if self.current_page > self.total_pages:
            self.current_page = max(1, self.total_pages)
        start = (self.current_page - 1) * self.page_size
        end = start + self.page_size
        return filtered[start:end]

    def set_page_size(self, size: int) -> None:
        if size.is_integer():
            self.page_size = size
            self.current_page = 1
            self.notify("data_changed")

    def go_to_page(self, page_num: int) -> None:
        if 1 <= page_num <= self.total_pages:
            self.current_page = page_num
            self.notify("data_changed")

    # ------------------------------------------------------------------
    # Data Operations
    # ------------------------------------------------------------------

    def load(self) -> None:
        """Fetch all records synchronously from service."""
        self.is_loading = True
        try:
            records = self._service.load()
            with self._data_lock:
                self._all_records = list(records)
                # Keep selected record in sync if still present
                if self._selected_record:
                    sel_id = self._selected_record.get(SC.K_ID)
                    found = next((r for r in self._all_records if r.get(SC.K_ID) == sel_id), None)
                    self._selected_record = found
            self._error_message = ""
        except Exception as exc:
            tb = traceback.format_exc()
            LoggerUtil.get_logger().error(f"MegawanMetronetViewModel load error: {exc}\n{tb}")
            self.error_message = "Lỗi tải dữ liệu"
        finally:
            self.is_loading = False
            self.notify("data_changed")
            self.notify("selected_record_changed")

    def load_in_background(self, page) -> None:
        if self._is_loading:
            return
        page.run_thread(self.load)

    def create_record(self, data: dict) -> bool:
        self.is_loading = True
        try:
            new_rec = self._service.create_record(data)
            self.load()
            self.set_selected_record(None)
            self.success_message = "Tạo mới bản ghi thành công"
            return True
        except Exception as exc:
            tb = traceback.format_exc()
            LoggerUtil.get_logger().error(f"MegawanMetronetViewModel create_record error: {exc}\n{tb}")
            self.error_message = f"Lỗi tạo bản ghi"
            return False
        finally:
            self.is_loading = False

    def update_record(self, record_id: int, data: dict) -> bool:
        self.is_loading = True
        try:
            updated_rec = self._service.update_record(record_id, data)
            self.load()
            self.set_selected_record(updated_rec)
            self.success_message = "Cập nhật bản ghi thành công"
            return True
        except Exception as exc:
            tb = traceback.format_exc()
            LoggerUtil.get_logger().error(f"MegawanMetronetViewModel update_record error: {exc}\n{tb}")
            self.error_message = f"Lỗi cập nhật bản ghi"
            return False
        finally:
            self.is_loading = False

    def delete_record(self, record_id: int) -> bool:
        self.is_loading = True
        try:
            ok = self._service.delete_record(record_id)
            if ok:
                if self._selected_record and self._selected_record.get(SC.K_ID) == record_id:
                    self.set_selected_record(None)
                self.load()
                self.success_message = "Xóa bản ghi thành công"
                return True
            else:
                self.error_message = "Không tìm thấy bản ghi để xóa"
                return False
        except Exception as exc:
            tb = traceback.format_exc()
            LoggerUtil.get_logger().error(f"MegawanMetronetViewModel delete_record error: {exc}\n{tb}")
            self.error_message = f"Lỗi xóa bản ghi"
            return False
        finally:
            self.is_loading = False

    def export_to_excel(self, folder_path: str) -> None:
        self.is_loading = True
        self._success_message = ""
        self._error_message = ""
        self._path_message = ""
        self.notify("status_changed")

        try:
            records = self.filtered_records
            out_file = self._service.export_to_excel(records, folder_path)
            self._path_message = out_file
            self._success_message = f"Xuất {len(records)} bản ghi thành công → {out_file}"
            self._error_message = ""
        except Exception as exc:
            tb = traceback.format_exc()
            LoggerUtil.get_logger().error(f"MegawanMetronetViewModel export_to_excel error: {exc}\n{tb}")
            self.error_message = f"Lỗi xuất Excel"
            self._path_message = ""
            self._success_message = ""
        finally:
            self.is_loading = False
            self.notify("status_changed")

    def get_db_update_list(self) -> list[str]:
        return [SC.K_EXCEL_MEGAWAN]
