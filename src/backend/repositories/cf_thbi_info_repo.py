from typing import List

from backend.models.cf_thiet_bi_info import ThBiInfo
from backend.repositories.base_repo import BaseRepository
from share.constant import constant as SC
from share.util.logger_util import LoggerUtil


class ThietBiInfoRepo(BaseRepository[ThBiInfo]):
    """Data access layer."""

    def __init__(self) -> None:
        super().__init__(ThBiInfo)

class ThietBiInfoService:
    """Business logic layer."""

    def __init__(self) -> None:
        self._repo = ThietBiInfoRepo()
        self.all_record: List[dict] = []
        self.card_dict = {}
        self.sfp_dict = {}
        self.dong_card_dict = {}

        self.card_xgspon_set: set = set()
        self.dong_card_tich_hop_set: set = set()

    def load(self) -> List[dict]:
        ret: List[ThBiInfo] = self._repo.get_all()

        all_record: List[dict] = [record.to_dict() for record in ret]

        self.all_record = all_record

        for item in self.all_record:
            if str(item[SC.K_PHAN_LOAI]).lower() == SC.K_CARD:
                self.card_dict[item[SC.K_TEN_CARD]] = item

                if str(item[SC.K_LOAI_CARD]).lower() == 'combo':
                    self.card_xgspon_set.add(item[SC.K_TEN_CARD])

                if str(item[SC.K_DONG_CARD]).lower() not in [None, ""]:
                    self.dong_card_dict[item[SC.K_DONG_CARD]] = item

                if str(item[SC.K_LOAI]).lower() == 'tich_hop':
                    self.dong_card_tich_hop_set.add(item[SC.K_DONG_CARD])

                continue

            if str(item[SC.K_PHAN_LOAI]).lower() == SC.K_SFP:
                self.sfp_dict[item[SC.K_SFP_MODEL_PN]] = item
                continue

    def get_all(self) -> List[dict]:
        record_list: List[ThBiInfo] = self._repo.get_all()

        return [item.to_dict() for item in record_list]