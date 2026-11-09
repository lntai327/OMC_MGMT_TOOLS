from typing import List, Optional

from backend.models.megawan_metronet.megawan_metronet_md import MegawanMetronetMd
from backend.repositories.base_repo import BaseRepository
from backend.repositories.base_service import BaseService
from share.constant import constant as SC
from share.util.logger_util import LoggerUtil
from share.util.time_util import TimeUtil

class MegawanMetronetRepo(BaseRepository[MegawanMetronetMd]):
    def __init__(self) -> None:
        super().__init__(MegawanMetronetMd)

    def _get_unique_key_column_dict(self) -> dict:
        return {
            MegawanMetronetMd.last_update: SC.K_LAST_UPDATE,
            MegawanMetronetMd.ma_tb: SC.K_MA_TB,
            MegawanMetronetMd.ma_lt_ma_tb_sub: SC.K_MA_LT_MA_TB_SUB,
            MegawanMetronetMd.ten_th_bao: SC.K_TEN_TH_BAO,
            MegawanMetronetMd.dia_chi: SC.K_DIA_CHI,
            MegawanMetronetMd.diem_cuoi: SC.K_DIEM_CUOI,
            MegawanMetronetMd.ip_src: SC.K_IP_SRC,
            MegawanMetronetMd.ip_des: SC.K_IP_DES,
            MegawanMetronetMd.svlan_cvlan: SC.K_SVLAN_CVLAN,
            MegawanMetronetMd.cap_adsl: SC.K_CAP_ADSL,
            MegawanMetronetMd.cap_odf: SC.K_CAP_ODF,
            MegawanMetronetMd.ghi_chu: SC.K_GHI_CHU,
            MegawanMetronetMd.ip: SC.K_IP,
            MegawanMetronetMd.ten_he_thong: SC.K_TEN_HE_THONG,
            MegawanMetronetMd.port_switch: SC.K_PORT_SWITCH,
            MegawanMetronetMd.upe: SC.K_UPE,
            MegawanMetronetMd.loai_hinh_tb: SC.K_LOAI_HINH_TB,
            MegawanMetronetMd.trang_thai: SC.K_TRANG_THAI,
            MegawanMetronetMd.toc_do: SC.K_TOC_DO,
            MegawanMetronetMd.don_vi: SC.K_DVI,
            MegawanMetronetMd.loai_kenh: SC.K_LOAI_KENH,
        }


class MegawanService(BaseService):
    _model_class = MegawanMetronetMd

    DATA_FIELDS = [
        SC.K_LAST_UPDATE,
        SC.K_MA_TB,
        SC.K_MA_LT_MA_TB_SUB,
        SC.K_TEN_TH_BAO,
        SC.K_DIA_CHI,
        SC.K_DIEM_CUOI,
        SC.K_IP_SRC,
        SC.K_IP_DES,
        SC.K_SVLAN_CVLAN,
        SC.K_CAP_ADSL,
        SC.K_CAP_ODF,
        SC.K_GHI_CHU,
        SC.K_IP,
        SC.K_TEN_HE_THONG,
        SC.K_PORT_SWITCH,
        SC.K_UPE,
        SC.K_LOAI_HINH_TB,
        SC.K_TRANG_THAI,
        SC.K_TOC_DO,
        SC.K_DVI,
        SC.K_LOAI_KENH,
    ]

    def __init__(self) -> None:
        self._repo = MegawanMetronetRepo()
        self.all_record: List[dict] = []

    def _get_excel_config(self):
        return (SC.K_EXCEL_MEGAWAN, SC.K_SHEET_DATA, 1)

    def _get_unique_record_key(self) -> List:
        return [
            SC.K_LAST_UPDATE,
            SC.K_MA_TB,
            SC.K_MA_LT_MA_TB_SUB,
            SC.K_TEN_TH_BAO,
            SC.K_DIA_CHI,
            SC.K_DIEM_CUOI,
            SC.K_IP_SRC,
            SC.K_IP_DES,
            SC.K_SVLAN_CVLAN,
            SC.K_CAP_ADSL,
            SC.K_CAP_ODF,
            SC.K_GHI_CHU,
            SC.K_IP,
            SC.K_TEN_HE_THONG,
            SC.K_PORT_SWITCH,
            SC.K_UPE,
            SC.K_LOAI_HINH_TB,
            SC.K_TRANG_THAI,
            SC.K_TOC_DO,
            SC.K_DVI,
            SC.K_LOAI_KENH,
        ]

    def _get_data_payload_key(self) -> List:
        return self.DATA_FIELDS

    def load(self) -> List[dict]:
        ret: List[MegawanMetronetMd] = self._repo.get_all()
        self.all_record = [record.to_dict() for record in ret]

        return self.all_record

    def create_record(self, data: dict) -> dict:
        # Sanitize data to include only recognized model columns
        payload = {k: str(data.get(k, "")).strip() for k in self.DATA_FIELDS if k in data}
        payload[SC.K_LAST_UPDATE] = TimeUtil().get_detail_current_time_str()
        new_obj = self._repo.create(payload)
        return new_obj.to_dict()

    def update_record(self, record_id: int, data: dict) -> Optional[dict]:
        payload = {k: str(data.get(k, "")).strip() for k in self.DATA_FIELDS if k in data}
        payload[SC.K_LAST_UPDATE] = TimeUtil().get_detail_current_time_str()
        updated_obj = self._repo.update_by_id(record_id, payload)
        return updated_obj.to_dict() if updated_obj else None

    def delete_record(self, record_id: int) -> bool:
        return self._repo.delete_by_id(record_id)