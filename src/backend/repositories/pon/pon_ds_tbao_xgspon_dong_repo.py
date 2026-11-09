from typing import List
from collections import defaultdict

from backend.models.pon.pon_ds_tbao_xgspon_dong_md import DsTbaoXgsponDongMd
from backend.repositories.base_repo import BaseRepository
from backend.repositories.base_service import BaseService
from backend.repositories.pon.pon_ds_tbao_xgspon_tay_repo import DsTbaoXgsponTayService
from backend.repositories.pon.pon_rp_card_access_repo import RpCardAccessService
from backend.repositories.cf_thbi_info_repo import ThietBiInfoService
from share.constant import constant as SC
from share.util.logger_util import LoggerUtil
from share.util.dynamic_info_util import DynamicInfoUtil
from share.constant import type as ST

#BDH 187 Chi tiet phat trien Fiber XGSPON ONT XGSPON dung trong.xlsx
class DsTbaoXgsponDongRepo(BaseRepository[DsTbaoXgsponDongMd]):
    def __init__(self) -> None:
        super().__init__(DsTbaoXgsponDongMd)

    def _get_unique_key_column_dict(self) -> dict:
        return {
            DsTbaoXgsponDongMd.ten_he_thong: SC.K_TEN_HE_THONG,
            DsTbaoXgsponDongMd.slot: SC.K_SLOT,
            DsTbaoXgsponDongMd.port: SC.K_PORT,
            DsTbaoXgsponDongMd.th_bao: SC.K_THBAO,
        }

class DsTbaoXgsponDongService(BaseService):
    _model_class = DsTbaoXgsponDongMd

    def __init__(self) -> None:
        self._repo = DsTbaoXgsponDongRepo()

        self.all_record: List[dict] = []
        self.ds_thbao_xgspon_dict_by_ten_hthong: dict = {}
        self.ds_thbao_xgspon_dict_by_ten_hthong_port: dict = {}
        self.warning_xgspon_records: List[dict] = []

        self._site = None

        self._rp_card_access_service = RpCardAccessService()
        self._thbi_info_service = ThietBiInfoService()

    def _get_excel_config(self):
        return (SC.K_EXCEL_DS_THBAO_XGSPON_DONG, SC.K_SHEET_DATA, 1)

    def _get_unique_record_key(self) -> List:
        return [
            SC.K_TEN_HE_THONG,
            SC.K_SLOT,
            SC.K_PORT,
            SC.K_THBAO,
        ]

    def _get_data_payload_key(self) -> List:
        return [
            SC.K_TRAM,
            SC.K_THBAO,
            SC.K_KH_HANG,
            SC.K_DIA_CHI,
            SC.K_TEN_HE_THONG,
            SC.K_SLOT,
            SC.K_PORT,
            SC.K_VPI,
            SC.K_CONG_NGHE,
        ]

    def _get_must_valid_record_key(self) -> List:
        return [
            SC.K_TEN_HE_THONG,
        ]

    def load(self) -> List[dict]:
        self._rp_card_access_service.load()
        self._thbi_info_service.load()

        self._site = DynamicInfoUtil().get_value(2, SC.K_SCREEN_INPUT, SC.K_SITE1)

        self.warning_xgspon_records.clear()

        ### Load record
        all_record_dong: list[dict] = []
        all_record_tay: list[dict] = []

        # Dong
        if self._site.lower() != ST.Site.TAY.value:
            ret: List[DsTbaoXgsponDongMd] = self._repo.get_all()
            all_record_dong: List[dict] = [record.to_dict() for record in ret]

            for item in all_record_dong:
                ten_hthong: str = item[SC.K_TEN_HE_THONG]

                if ".olt." not in ten_hthong.lower():
                    continue

                if str(item[SC.K_CONG_NGHE]).lower() == "xgspon":

                    item[SC.K_ONU] = item[SC.K_VPI]

        # Tay
        if self._site.lower() != ST.Site.DONG.value:
            ds_tbao_xgspon_tay = DsTbaoXgsponTayService()
            ds_tbao_xgspon_tay.load()
            all_record_tay = ds_tbao_xgspon_tay.all_record

        ###
        _dict_by_ten_hthong = defaultdict(lambda: {
            SC.K_SL_THBAO: 0,
        })

        _dict_by_ten_hthong_port = defaultdict(lambda: {
            SC.K_SL_THBAO: 0,
        })

        self.all_record = all_record_dong + all_record_tay

        for item in self.all_record:
            ten_hthong: str = item[SC.K_TEN_HE_THONG]

            if ".olt." not in ten_hthong.lower():
                continue

            if str(item[SC.K_CONG_NGHE]).lower() != "xgspon":
                continue

            slot = str(item.get(SC.K_SLOT, "N/A"))
            try:
                slot = str(int(slot))
            except:
                pass

            #
            card_by_slot_only: dict = self._rp_card_access_service\
                .rp_card_access_dict_by_ten_hthong_slot_only\
                .get(
                    (ten_hthong, f'{slot}'), {}
                )

            # Fill Frame
            item[SC.K_FRAME] = 0 if str(card_by_slot_only.get(SC.K_HANG_SX)).strip().lower() == "huawei" \
                else 1

            ### FILTER Card không tồn tại

            if not card_by_slot_only:
                item[SC.K_GHI_CHU] = "[loại] ds tbao xgspon : th_bao trên Card không tồn tại"
                self.warning_xgspon_records.append(item)

                continue

            last_serial_card = card_by_slot_only.get(SC.K_LAST_SERIAL, "N/A")
            last_valid_serial_card = card_by_slot_only.get(SC.K_LAST_VALID_SERIAL, "N/A")
            if last_serial_card in ["", None]:
                if last_valid_serial_card in ["", None]:
                    item[SC.K_GHI_CHU] = "[loại] ds tbao xgspon : th_bao trên Card chưa từng có Serial"
                    self.warning_xgspon_records.append(item)

                    continue
                else:
                    item[SC.K_GHI_CHU] = "[*giữ] ds tbao xgspon : th_bao trên Card hiện tại không có Serial"
                    self.warning_xgspon_records.append(item)

            ###
            port = str(item.get(SC.K_PORT, "N/A"))
            try:
                port = str(int(port))
            except:
                pass

            dong_card = \
                card_by_slot_only \
                .get(
                    SC.K_DONG, None
                )

            ten_card = \
                card_by_slot_only \
                .get(
                    SC.K_TEN_CARD, "N/A"
                )

            #
            if ten_card and (str(ten_card).lower() != "onboard"):
                loai_card = self._thbi_info_service.card_dict\
                        .get(ten_card, {})\
                        .get(SC.K_LOAI_CARD, "N/A")
            else:
                loai_card = self._thbi_info_service.dong_card_dict\
                        .get(dong_card, {})\
                        .get(SC.K_LOAI_CARD, "N/A")

            if loai_card and (str(loai_card).lower() == "combo"):
                _dict_by_ten_hthong[ten_hthong][SC.K_SL_THBAO] += 1
                _dict_by_ten_hthong_port[(ten_hthong, slot, port)][SC.K_SL_THBAO] += 1
            else:
                # LoggerUtil.get_logger().warning(
                #     f"{self.__class__.__name__} tbao xgspon : {ten_hthong} slot: {slot} ten_card: {ten_card} dong_card: {dong_card} loai_card: {loai_card} is not combo"
                # )

                item[SC.K_GHI_CHU] = "[loại] ds tbao xgspon : thbao trên card không phải combo"

                self.warning_xgspon_records.append(item)

        #
        self.ds_thbao_xgspon_dict_by_ten_hthong = \
            _dict_by_ten_hthong

        self.ds_thbao_xgspon_dict_by_ten_hthong_port = \
            _dict_by_ten_hthong_port