from typing import List, Optional

from backend.models.pon.pon_thbi_access import ThbiAccessMd
from backend.repositories.base_repo import BaseRepository
from backend.repositories.base_service import BaseService
from share.constant import constant as SC
from share.util.logger_util import LoggerUtil
from share.util.time_util import TimeUtil


class ThbiAccessRepo(BaseRepository[ThbiAccessMd]):
    """Data access layer."""

    def __init__(self) -> None:
        super().__init__(ThbiAccessMd)

    def _get_unique_key_column_dict(self) -> dict:
        return {
            ThbiAccessMd.ten_he_thong: SC.K_TEN_HE_THONG
        }

class ThbiAccessService(BaseService):
    """Business logic layer."""

    _model_class = ThbiAccessMd

    def __init__(self) -> None:
        self._repo = ThbiAccessRepo()
        self.all_record: List[dict] = []
        self.thbi_access_dict_by_ten_hthong: dict = {}

    def _get_excel_config(self):
        return (SC.K_EXCEL_THBI_ACCESS, SC.K_SHEET_DATA, 1)

    def _get_unique_record_key(self) -> List:
        return [SC.K_TEN_HE_THONG,]

    def _get_data_payload_key(self) -> List:
        return [
            SC.K_MA_CSHT,
            SC.K_TEN_HE_THONG,
            SC.K_CHUC_NANG,
            SC.K_IP,
            SC.K_DONG,
        ]

    def _filter_record(self, record: dict) -> bool:
        """Only keep records with chuc_nang == 'gpon'."""
        return str(record.get(SC.K_CHUC_NANG, "")).lower() == "gpon"

    def load(self) -> List[dict]:
        ret: List[ThbiAccessMd] = self._repo.get_all()

        self.all_record: List[dict] = [record.to_dict() for record in ret]

        _dict = {}
        for item in self.all_record:
            _dict[item[SC.K_TEN_HE_THONG]] = item

        self.thbi_access_dict_by_ten_hthong = _dict