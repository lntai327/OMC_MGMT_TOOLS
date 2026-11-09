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

    def create(
        self,
        ma_csht: str,
        ten_csht: str,
        ten_dvi_qly: str,
        ten_ttvt_tram_vthong_netx: str,
        loai_nha_tram: str,
        tr_thai_dat_may_no: str,
        phuong_xa: str,
        dia_chi: str,
        ma_loai_csht_ddong: str,
        trang_thai: str,
    ) -> dict:
        if not ma_csht or not ma_csht.strip():
            LoggerUtil.get_logger().error(
                "CshtCclService create: Tên hệ thống không được rỗng.")
            raise ValueError("Tên hệ thống không được rỗng.")
        data = {
            SC.K_MA_CSHT: ma_csht.strip(),
            SC.K_TEN_CSHT: ten_csht.strip(),
            SC.K_TEN_DVI_QLY: ten_dvi_qly.strip(),
            SC.K_TEN_TTVT_TRAM_VT_NETX: ten_ttvt_tram_vthong_netx.strip(),
            SC.K_LOAI_NHA_TRAM: loai_nha_tram.strip(),
            SC.K_TRTHAI_DAT_MNO: tr_thai_dat_may_no.strip(),
            SC.K_PHUONG_XA: phuong_xa.strip(),
            SC.K_DIA_CHI: dia_chi.strip(),
            SC.K_MA_LOAI_CSHT_DDONG: ma_loai_csht_ddong.strip(),
            SC.K_TRANG_THAI: trang_thai.strip(),
        }

        record = self._repo.create(data)
        return record.to_dict()

    def update(
        self,
        ma_csht: str,
        ten_csht: str,
        ten_dvi_qly: str,
        ten_ttvt_tram_vthong_netx: str,
        loai_nha_tram: str,
        tr_thai_dat_may_no: str,
        phuong_xa: str,
        dia_chi: str,
        ma_loai_csht_ddong: str,
        trang_thai: str,
    ) -> Optional[dict]:
        if not ma_csht or not ma_csht.strip():
            raise ValueError("CshtCclService ma_csht cannot be empty.")

        data: dict[str, str] = {
            SC.K_MA_CSHT: ma_csht.strip(),
            SC.K_TEN_CSHT: ten_csht.strip(),
            SC.K_TEN_DVI_QLY: ten_dvi_qly.strip(),
            SC.K_TEN_TTVT_TRAM_VT_NETX: ten_ttvt_tram_vthong_netx.strip(),
            SC.K_LOAI_NHA_TRAM: loai_nha_tram.strip(),
            SC.K_TRTHAI_DAT_MNO: tr_thai_dat_may_no.strip(),
            SC.K_PHUONG_XA: phuong_xa.strip(),
            SC.K_DIA_CHI: dia_chi.strip(),
            SC.K_MA_LOAI_CSHT_DDONG: ma_loai_csht_ddong.strip(),
            SC.K_TRANG_THAI: trang_thai.strip(),
            SC.K_LAST_UPDATE: TimeUtil().get_detail_current_time_str(),
        }

        record = self._repo.update_by_keys(
            {SC.K_MA_CSHT: data[SC.K_MA_CSHT]},
            data
        )
        return record.to_dict() if record else None