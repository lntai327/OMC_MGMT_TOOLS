import re
from typing import List
from collections import defaultdict

from cycler import V

from backend.models.pon.pon_rp_trans_access_by_unit import RpTransAccessMd
from backend.repositories.base_repo import BaseRepository
from backend.repositories.base_service import BaseService
from backend.repositories.cf_thbi_info_repo import ThietBiInfoService
from share.constant import constant as SC
from share.util.logger_util import LoggerUtil


class RpTransAccessRepo(BaseRepository[RpTransAccessMd]):
    """Data access layer."""

    def __init__(self) -> None:
        super().__init__(RpTransAccessMd)

    def _get_unique_key_column_dict(self) -> dict:
        return {
            RpTransAccessMd.ten_he_thong: SC.K_TEN_HE_THONG,
            RpTransAccessMd.vi_tri: SC.K_VI_TRI
        }
class RpTransAccessService(BaseService):
    """Business logic layer."""

    _model_class = RpTransAccessMd
    _SLOT_PON_PATTERN = re.compile(r"^pon:\d+/\d+/(\d+)/(\d+)$", re.IGNORECASE) #pon:1/1/2/1
    _SLOT_GPON_PATTERN_1 = re.compile(r"^gpon_\d+/(\d+)/(\d+)$", re.IGNORECASE) #gpon_1/3/3
    _SLOT_GPON_PATTERN_2 = re.compile(r"^gpon \d+/(\d+)/(\d+)$", re.IGNORECASE) #GPON 0/1/4
    _SLOT_GPON_PATTERN_3 = re.compile(r"^port(\d+)(?:-|$)", re.IGNORECASE) #Port3(abc)

    def __init__(self) -> None:
        self._repo = RpTransAccessRepo()
        self.all_record: List[dict] = []
        self.rp_trans_access_dict_by_ten_hthong: dict = {}
        self.rp_trans_access_dict_by_ten_hthong_slot: dict = {}

        self._thbi_info_service = ThietBiInfoService()
        self._thbi_info_service.load()

    def _get_excel_config(self):
        return (SC.K_EXCEL_RP_TRANS_BY_UNIT, SC.K_SHEET_DATA, 2)

    def _get_unique_record_key(self) -> List:
        return [SC.K_TEN_HE_THONG, SC.K_VI_TRI,]

    def _get_data_payload_key(self) -> List:
        return [
            SC.K_TEN_HE_THONG,
            SC.K_MODEL,
            SC.K_SERIAL,
            SC.K_VI_TRI,
        ]

    def load(self) -> List[dict]:
        ret: List[RpTransAccessMd] = self._repo.get_all()

        all_record: List[dict] = [record.to_dict() for record in ret]

        self.all_record = all_record

        _dict_by_ten_hthong = defaultdict(lambda: {
            SC.K_SL_SFP_XGSPON: 0,
        })
        _dict_by_ten_hthong_slot = {}

        sfp_combo_model_pn_set_lower = {
            k.lower() for k, v in self._thbi_info_service.sfp_dict.items()
            if str(v.get(SC.K_LOAI_SFP, "N/A")).lower() in ["mpm", "n2"]
        }
        for item in self.all_record:
            if str(item.get(SC.K_MODEL)).lower() in sfp_combo_model_pn_set_lower:
                _dict_by_ten_hthong[item[SC.K_TEN_HE_THONG]][SC.K_SL_SFP_XGSPON] += 1

            ret = self._parse_slot_gpon(item.get(SC.K_VI_TRI, None))
            if ret:
                slot, port = ret
                _dict_by_ten_hthong_slot[(item[SC.K_TEN_HE_THONG], str(slot), str(port))] = item

        self.rp_trans_access_dict_by_ten_hthong = _dict_by_ten_hthong
        self.rp_trans_access_dict_by_ten_hthong_slot = _dict_by_ten_hthong_slot

    def _parse_slot_gpon(self, value: str) -> tuple[int|str, int] | None:
        if not value:
            return None

        for pattern in (
            self._SLOT_PON_PATTERN,
            self._SLOT_GPON_PATTERN_1,
            self._SLOT_GPON_PATTERN_2,
        ):
            match = pattern.fullmatch(value)

            if match:
                slot = int(match.group(1))
                port = int(match.group(2))

                return slot, port
        
        #
        for pattern in (
            self._SLOT_GPON_PATTERN_3,
        ):
            
            match = pattern.match(value)

            if match:
                slot = ""
                port = int(match.group(1))

                return slot, port

        return None