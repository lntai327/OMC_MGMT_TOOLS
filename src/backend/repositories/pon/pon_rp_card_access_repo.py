from typing import List

from backend.models.pon.pon_rp_card_access_by_unit import RpCardAccessMd
from backend.repositories.base_repo import BaseRepository
from backend.repositories.base_service import BaseService
from backend.repositories.cf_thbi_info_repo import ThietBiInfoService
from backend.util.ex_handle_util import ExcelHandleUtil
from share.constant import constant as SC
from share.util.logger_util import LoggerUtil
from share.util.convert import to_int

from share.util.dynamic_info_util import DynamicInfoUtil
from share.util.explorer_util import ExplorerUtil

class RpCardAccessRepo(BaseRepository[RpCardAccessMd]):
    """Data access layer."""

    def __init__(self) -> None:
        super().__init__(RpCardAccessMd)

    def _get_unique_key_column_dict(self) -> dict:
        return {
            RpCardAccessMd.ten_he_thong: SC.K_TEN_HE_THONG,
            RpCardAccessMd.slot: SC.K_SLOT
        }

class RpCardAccessService(BaseService):
    """Business logic layer."""

    _model_class = RpCardAccessMd

    def __init__(self) -> None:
        self._repo = RpCardAccessRepo()
        self.all_record: List[dict] = []
        self.rp_card_access_dict_by_ten_hthong: dict = {}
        self.rp_card_access_dict_by_ten_hthong_slot_only: dict = {}

        self._thbi_info_service = ThietBiInfoService()
        self._thbi_info_service.load()

        self._ten_card_valid_set_lower = {
            ten_card.lower() for ten_card in self._thbi_info_service.card_dict.keys()
        }
        self._ten_card_xgspon_set_lower = {
            ten_card.lower() for ten_card in self._thbi_info_service.card_xgspon_set
        }
        self._dong_card_tich_hop_set_lower = {
            dong_card.lower() for dong_card in self._thbi_info_service.dong_card_tich_hop_set
        }

    def _get_excel_config(self):
        return (SC.K_EXCEL_RP_CARD_BY_UNIT, SC.K_SHEET_DATA, 2)

    def _get_unique_record_key(self) -> List:
        return [SC.K_TEN_HE_THONG, SC.K_SLOT,]

    def _get_data_payload_key(self) -> List:
        return [
            SC.K_TEN_HE_THONG,
            SC.K_SLOT,
            SC.K_TEN_CARD,
            SC.K_LAST_SERIAL,
            SC.K_DONG,
            SC.K_HANG_SX,
            SC.K_LAST_VALID_SERIAL,
        ]
    
    def _get_must_valid_record_key(self) -> List:
        return [
            SC.K_TEN_HE_THONG,
            SC.K_SLOT,
        ]

    def import_from_excel(self) -> dict:
        excel_info_key, sheet_info_key, header_row_range = self._get_excel_config()

        excel_path = ExplorerUtil().get_cache_file_path(
            DynamicInfoUtil().get_value(2, excel_info_key, SC.K_NAME)
        )

        sheet_name_value = DynamicInfoUtil().get_value(
            4, excel_info_key, SC.K_REQUIRE_SHEET,
            sheet_info_key, SC.K_NAME
        )

        sheet_names = sheet_name_value

        # Load data from all matching sheets
        record_list: list[dict] = []
        for sheet_name in sheet_names:
            load_kwargs = dict(
                sheet_name=sheet_name,
                sheet_info_key=sheet_info_key,
                excel_info_key=excel_info_key,
                excel_path=excel_path,
            )
            if header_row_range > 1:
                load_kwargs["header_row_range"] = header_row_range

            sheet_records = ExcelHandleUtil().load_items(**load_kwargs)
            LoggerUtil.get_logger().info(
                f"{self.__class__.__name__} loaded {len(sheet_records)} records from sheet '{sheet_name}'"
            )
            record_list.extend(sheet_records)

        # Parse raw records through model
        raw_records = [self._model_class().load(x).to_dict() for x in record_list]
        normalize_raw_dict_by_ten_hthong_slot_only = {}

        for item in raw_records:
            ten_he_thong = item[SC.K_TEN_HE_THONG]
            slot: str = item.get(SC.K_SLOT, "N/A")
            ten_card: str = item.get(SC.K_TEN_CARD, "N/A")

            if ten_card.lower() not in self._ten_card_valid_set_lower:
                continue

            ###
            slot_only = slot.strip().split("/")[-1].strip()
            if slot_only:
                normalize_raw_dict_by_ten_hthong_slot_only[(ten_he_thong, slot_only)] = item

        # Normalize
        ## Get current record in db
        self.load()

        for k, normalize_raw_record in normalize_raw_dict_by_ten_hthong_slot_only.items():
            last_valid_serial_in_current_db: str = (
                self.rp_card_access_dict_by_ten_hthong_slot_only
                .get(k, {})
                .get(SC.K_LAST_VALID_SERIAL, "")
            ) or ""

            last_serial: str = normalize_raw_record.get(SC.K_LAST_SERIAL, "")
            is_valid_last_serial = \
                last_serial and str(last_serial).strip() not in ("", "N/A", "None")

            normalize_raw_record[SC.K_LAST_VALID_SERIAL] = (
                last_serial if is_valid_last_serial else last_valid_serial_in_current_db
            )

        return self._import_upsert(
            list(normalize_raw_dict_by_ten_hthong_slot_only.values())
        )

    def load(self) -> List[dict]:
        ret: List[RpCardAccessMd] = self._repo.get_all()

        all_record: List[dict] = [record.to_dict() for record in ret]

        self.all_record = all_record

        _dict_by_ten_hthong = {}
        _dict_by_ten_hthong_slot_only = {}

        for item in self.all_record:
            ten_he_thong = item[SC.K_TEN_HE_THONG]
            slot: str = item.get(SC.K_SLOT, "N/A")
            ten_card: str = item.get(SC.K_TEN_CARD, "N/A")
            dong_card: str = item.get(SC.K_DONG, "N/A")

            if ten_card.lower() not in self._ten_card_valid_set_lower:
                continue

            ### normalize
            if dong_card.strip().lower() in self._dong_card_tich_hop_set_lower:
                item[SC.K_LAST_SERIAL] = "Card tích hợp"
                item[SC.K_LAST_VALID_SERIAL] = "Card tích hợp"

            ### _dict_by_ten_hthong_slot_only
            slot_only = slot.strip().split("/")[-1].strip()
            if slot_only:
                _dict_by_ten_hthong_slot_only[(ten_he_thong, slot_only)] = item

            ### _dict_by_ten_hthong
            data_dict_by_ten_hthong = _dict_by_ten_hthong.setdefault(
                ten_he_thong,
                {
                    SC.K_SLOT: set(), #set of slot num
                    SC.K_FRAME: set(), #set of frame num
                    SC.K_SL_CARD_XGSPON: 0,
                    SC.K_VTRI_CARD_XGSPON: "",
                    SC.K_TEN_CARD_XGSPON: set(), #set of str
                },
            )

            if ".olt." in ten_he_thong.lower():
                #
                data_dict_by_ten_hthong[SC.K_FRAME].add(
                    0 if str(item.get(SC.K_HANG_SX)).strip().lower() == "huawei"
                    else 1
                )
                data_dict_by_ten_hthong[SC.K_SLOT].add(to_int(slot_only, False))

                # XGSPON
                if ten_card.lower() in self._ten_card_xgspon_set_lower:

                    data_dict_by_ten_hthong[SC.K_SL_CARD_XGSPON] += 1

                    if slot:
                        data_dict_by_ten_hthong[SC.K_VTRI_CARD_XGSPON] = (
                            f"{data_dict_by_ten_hthong[SC.K_VTRI_CARD_XGSPON]}, {slot}"
                            if data_dict_by_ten_hthong[SC.K_VTRI_CARD_XGSPON]
                            else slot
                        )
                    else:
                        LoggerUtil.get_cur_logger().warning(
                            f"Slot is empty for ten_he_thong xgspon: {ten_he_thong}, ten_card: {ten_card}"
                        )

                    data_dict_by_ten_hthong[SC.K_TEN_CARD_XGSPON].add(ten_card)

        self.rp_card_access_dict_by_ten_hthong = _dict_by_ten_hthong
        self.rp_card_access_dict_by_ten_hthong_slot_only = _dict_by_ten_hthong_slot_only