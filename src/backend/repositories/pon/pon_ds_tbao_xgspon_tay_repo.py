from typing import List

from backend.models.pon.pon_ds_tbao_xgspon_tay_md import DsTbaoXgsponTayMd
from backend.repositories.base_repo import BaseRepository
from backend.repositories.base_service import BaseService
from share.constant import constant as SC
from share.util.logger_util import LoggerUtil

#4_GLI_001_5_Báo_cáo_thuê_bao_sử_dụng_thiết_bị_XGSPON_đơn_vị_VT_20261007.xlsx
class DsTbaoXgsponTayRepo(BaseRepository[DsTbaoXgsponTayMd]):
    """Data access layer."""

    def __init__(self) -> None:
        super().__init__(DsTbaoXgsponTayMd)

    def _get_unique_key_column_dict(self) -> dict:
        return {
            DsTbaoXgsponTayMd.ten_he_thong: SC.K_TEN_HE_THONG,
            DsTbaoXgsponTayMd.slot: SC.K_SLOT,
            DsTbaoXgsponTayMd.port: SC.K_PORT,
            DsTbaoXgsponTayMd.th_bao: SC.K_THBAO,
        }

class DsTbaoXgsponTayService(BaseService):
    _model_class = DsTbaoXgsponTayMd

    def __init__(self) -> None:
        self._repo = DsTbaoXgsponTayRepo()

        self.all_record: List[dict] = []

    def _get_excel_config(self):
        return (SC.K_EXCEL_DS_THBAO_XGSPON_TAY, SC.K_SHEET_DATA, 1)

    def _get_unique_record_key(self) -> List:
        return [
            SC.K_TEN_HE_THONG,
            SC.K_SLOT,
            SC.K_PORT,
            SC.K_THBAO,
        ]

    def _get_data_payload_key(self) -> List:
        return [
            SC.K_THBAO,
            SC.K_KH_HANG,
            SC.K_DIA_CHI,
            SC.K_TEN_HE_THONG,
            SC.K_SLOT,
            SC.K_PORT,
            SC.K_CONG_NGHE,
        ]

    def _get_must_valid_record_key(self) -> List:
        return [
            SC.K_TEN_HE_THONG,
        ]

    def load(self) -> List[dict]:
        ret: List[DsTbaoXgsponTayMd] = self._repo.get_all()

        all_record: List[dict] = [record.to_dict() for record in ret]

        # normalize
        for item in all_record:
            ten_hthong: str = item[SC.K_TEN_HE_THONG]

            if ".olt." not in ten_hthong.lower():
                continue

            if str(item[SC.K_CONG_NGHE]).lower() == "xgspon":

                item[SC.K_ONU] = ""

        #
        self.all_record = all_record