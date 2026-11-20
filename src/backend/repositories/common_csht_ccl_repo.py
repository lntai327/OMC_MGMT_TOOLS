### use for : BTS, CELL, XGSPON
from typing import List, Optional

from backend.models.common_csht_ccl import CshtCclMd
from backend.repositories.base_repo import BaseRepository
from backend.repositories.base_service import BaseService
from share.constant import constant as SC
from share.util.logger_util import LoggerUtil
from share.util.time_util import TimeUtil


class CshtCclRepo(BaseRepository[CshtCclMd]):
    """Data access layer."""

    def __init__(self) -> None:
        super().__init__(CshtCclMd)

    def _get_unique_key_column_dict(self) -> dict:
        return {CshtCclMd.ma_csht: SC.K_MA_CSHT}
class CshtCclService(BaseService):
    """Business logic layer."""

    _model_class = CshtCclMd

    def __init__(self) -> None:
        self._repo = CshtCclRepo()
        self.csht_mdsd_items_list_all: List[dict] = []
        self.csht_mdsd_items_ma_csht_dict: dict = {}

    def _get_excel_config(self):
        return (SC.K_EXCEL_CSHT_CCL_KEY, SC.K_SHEET_CSHT_MDSDL_KEY, 1)

    def _get_unique_record_key(self) -> List:
        return [SC.K_MA_CSHT,]

    def _get_data_payload_key(self) -> List:
        return [
            SC.K_MA_CSHT,
            SC.K_TEN_CSHT,
            SC.K_TEN_DVI_QLY,
            SC.K_TEN_TTVT_TRAM_VT_NETX,
            SC.K_LOAI_NHA_TRAM,
            SC.K_TRTHAI_DAT_MNO,
            SC.K_PHUONG_XA,
            SC.K_DIA_CHI,
            SC.K_MA_LOAI_CSHT_DDONG,
            SC.K_TRANG_THAI,
        ]

    def _filter_record(self, record: dict) -> bool:
        """Only keep records with trang_thai == 'đang hoạt động'."""
        return str(record.get(SC.K_TRANG_THAI, "")).lower() == "đang hoạt động"

    def load(self) -> List[dict]:
        ret: List[CshtCclMd] = self._repo.get_all()

        self.csht_mdsd_items_list_all: List[dict] = [record.to_dict() for record in ret]

        _dict = {}
        for item in self.csht_mdsd_items_list_all:
            _dict[item[SC.K_MA_CSHT]] = item

        self.csht_mdsd_items_ma_csht_dict = _dict