from typing import List
from collections import defaultdict
from itertools import chain
import re
from numpy import kaiser

from backend.models.pon.pon_bc_chi_tiet_onu import BcChiTietOnuMd
from backend.repositories.base_repo import BaseRepository
from backend.repositories.base_service import BaseService
from backend.repositories.pon.pon_tbao_fiber_theo_visa_dong_repo import TbaoFiberVisaDongService
from backend.repositories.pon.pon_tbao_fiber_theo_visa_tay_repo import TbaoFiberVisaTayService
from backend.repositories.pon.pon_rp_card_access_repo import RpCardAccessService
from backend.util.ex_handle_util import ExcelHandleUtil
from backend.repositories.common.excel_tht_ttvt.excel_tht_ttvt_maker import ExcelThtTtvtMaker
from backend.repositories.pon.pon_thbi_access_repo import ThbiAccessService
from backend.repositories.common_csht_ccl_repo import CshtCclService

from share.constant import constant as SC
from share.constant import type as ST
from share.util.convert import safe_sort_date_time, to_int
from share.util.dynamic_info_util import DynamicInfoUtil
from share.util.explorer_util import ExplorerUtil
from share.util.logger_util import LoggerUtil


class BcChTietOnuRepo(BaseRepository[BcChiTietOnuMd]):
    """Data access layer."""

    def __init__(self) -> None:
        super().__init__(BcChiTietOnuMd)

    def _get_unique_key_column_dict(self) -> dict:
        return {
            BcChiTietOnuMd.ten_he_thong: SC.K_TEN_HE_THONG,
            BcChiTietOnuMd.frame: SC.K_FRAME,
            BcChiTietOnuMd.slot: SC.K_SLOT,
            BcChiTietOnuMd.port: SC.K_PORT,
            BcChiTietOnuMd.onu: SC.K_ONU,
        }

class BcChTietOnuService(BaseService):
    """Business logic layer."""

    _model_class = BcChiTietOnuMd

    def __init__(self) -> None:
        self.all_valid_onu_record: List[dict] = []
        self.bc_chtiet_onu_dict_by_ten_hthong: dict = {}
        self.warning_onu_record: List[dict] = []

        self._repo = BcChTietOnuRepo()
        self._site = None

        self._tht_ttvt_service = ExcelThtTtvtMaker()
        self._thbi_access_service = ThbiAccessService()
        self._rp_card_access_service = RpCardAccessService()
        self._csht_ccl_service = CshtCclService()

    def _valid_site_by_ttvt(self, ttvt: str):
        # Fillter: Site
        match self._site.lower():
            case ST.Site.ALL_SITE.value:
                return True
            case ST.Site.DONG.value | ST.Site.TAY.value:
                try:
                    if str(self._tht_ttvt_service.ttvt_dict[str(ttvt).lower()][SC.K_SITE1]).lower() == \
                            str(self._site).lower():
                        return True
                    else:
                        return False
                except Exception as e:
                    LoggerUtil.get_logger().warning(
                        f'{self.__class__.__name__} _valid_site_by_ttvt failled : {ttvt}'
                        f' {SC.K_UI_MSG_NOT_DETECT_SITE} as {e}'
                    )
                    return None
            case _:
                LoggerUtil.get_logger.error("_valid_site_by_ttvt : Invalid site")
                return None

        return None

    def _get_excel_config(self):
        return (SC.K_EXCEL_BC_CHTIET_ONU, SC.K_SHEET_DATA, 1)

    def _get_unique_record_key(self) -> List:
        return [
            SC.K_TEN_HE_THONG,
            SC.K_FRAME,
            SC.K_SLOT,
            SC.K_PORT,
            SC.K_ONU,
            SC.K_SERIAL,
            SC.K_THBAO,
        ]

    def _get_data_payload_key(self) -> List:
        return [
            SC.K_TINH,
            SC.K_DVI_QLY,
            SC.K_TRAM,
            SC.K_TEN_HE_THONG,
            SC.K_IP,
            SC.K_FRAME,
            SC.K_SLOT,
            SC.K_PORT,
            SC.K_ONU,
            SC.K_SERIAL,
            SC.K_LOAI_ONU,
            SC.K_TEN_ONU,
            SC.K_THBAO,
            SC.K_DUPLICETED,
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

        # Add duplicated record counter
        raw_records_dict_by_unique_record_key = {}
        for rec in raw_records[:]:
            unique_rec_keys = self._get_unique_record_key()

            dict_key: tuple = (rec.get(v) for v in unique_rec_keys)

            if dict_key not in raw_records_dict_by_unique_record_key:
                rec[SC.K_DUPLICETED] = 1
                raw_records_dict_by_unique_record_key[dict_key] = rec
            else:
                raw_records_dict_by_unique_record_key[dict_key][SC.K_DUPLICETED] += 1

        return self._import_upsert(
            list(raw_records_dict_by_unique_record_key.values())
        )

    def load(self) -> List[dict]:
        self.all_valid_onu_record.clear()
        self.warning_onu_record.clear()

        self._site = DynamicInfoUtil().get_value(2, SC.K_SCREEN_INPUT, SC.K_SITE1)

        self._tht_ttvt_service.load()
        self._thbi_access_service.load()
        self._csht_ccl_service.load()
        self._rp_card_access_service.load()

        ret: List[BcChiTietOnuMd] = self._repo.get_all()

        bc_chtiet_onu_record_all: List[dict] = [record.to_dict() for record in ret]
        bc_chtiet_onu_olt_record: List[dict] = []
        bc_ds_tk_dv_olt_record: List[dict] = []

        ###################### Fillter VISA
        visa_dong_all_record: list[dict] = []
        visa_tay_all_record: list[dict] = []

        if self._site.lower() != ST.Site.TAY.value:
            visa_dong = TbaoFiberVisaDongService()
            visa_dong.load()
            visa_dong_all_record = visa_dong.all_record

        if self._site.lower() != ST.Site.DONG.value:
            visa_tay = TbaoFiberVisaTayService()
            visa_tay.load()
            visa_tay_all_record = visa_tay.all_record

        visa_all = visa_dong_all_record + visa_tay_all_record

        #SYSTEMID=BDH.TSN.BTH.OLT.AL11:-:RACKID=1:-:SELFID=1:-:SLOT=01:-:PORT=07:-:VPI=52:-:VCI=11
        _THAM_SO_PATTERN = re.compile(
            r"SYSTEMID=(?P<system_id>[^:-]+).*?"
            r"RACKID=(?P<rack_id>\d+).*?"
            r"SLOT=0*(?P<slot>\d+).*?"
            r"PORT=0*(?P<port>\d+).*?"
            r"VPI=0*(?P<vpi>\d+)"
        )

        for item in visa_all:
            tham_so = item.get(SC.K_THAM_SO, "")
            match = _THAM_SO_PATTERN.search(tham_so)
            if match:
                ten_he_thong = match.group("system_id")
                if ".olt." not in ten_he_thong.lower():
                    continue

                frame = to_int(match.group("rack_id"), False)
                slot = to_int(match.group("slot"), False)
                port = to_int(match.group("port"), False)
                onu = to_int(match.group("vpi"), False)

                item[SC.K_TEN_HE_THONG] = ten_he_thong
                item[SC.K_FRAME] = frame
                item[SC.K_SLOT] = slot
                item[SC.K_PORT] = port
                item[SC.K_ONU] = onu
 
                #
                item[SC.K_THBAO] = item[SC.K_T_KHOAN]
                item[SC.K_SRC] = "visa"

                bc_ds_tk_dv_olt_record.append(item)

            else:
                pass

        ### Fillter VISA : trùng ten_hthong, slot, user, trang thai -> lấy 1 record
        bc_ds_tk_dv_olt_dict_by_ten_hthong_slot_user = {}
        for item in bc_ds_tk_dv_olt_record[:]:
            duplicated_counter = item.get(SC.K_DUPLICETED)
            if to_int(duplicated_counter) > 1:
                # LoggerUtil.get_logger().warning(
                #     f"ds_tk_dv_hien_co : trùng tham_so, trang_thai, th_bao : {item}"
                # )
                item[SC.K_GHI_CHU] = "[*giữ 1] ds_tk_dv_hien_co(Visa) : trùng tham_so, trang_thai, th_bao"
                self.warning_onu_record.append(item)

            ten_he_thong = item.get(SC.K_TEN_HE_THONG)

            dict_key = (
                ten_he_thong,
                item.get(SC.K_FRAME),
                item.get(SC.K_SLOT),
                item.get(SC.K_PORT),
                item.get(SC.K_ONU),
                item.get(SC.K_THBAO),
                item.get(SC.K_TRANG_THAI),
            )

            if dict_key not in bc_ds_tk_dv_olt_dict_by_ten_hthong_slot_user:
                bc_ds_tk_dv_olt_dict_by_ten_hthong_slot_user[dict_key] = item
            else:
                LoggerUtil.get_logger().error(
                    f"bc_ds_tk_dv_olt_record [Must never occur] : trùng ten_hthong, frame, slot, port, onu_idx, th_bao, trang thai : {item}"
                )
                bc_ds_tk_dv_olt_record.remove(item)
                continue

            #
            if ten_he_thong not in self._thbi_access_service.thbi_access_dict_by_ten_hthong:
                LoggerUtil.get_logger().warning(
                    f"ds_tk_dv_hien_co(Visa) : ten_he_thong không có trong thiet_bi_access : {item}"
                )

                bc_ds_tk_dv_olt_record.remove(item)

                item[SC.K_GHI_CHU] = "[loại] bc_ds_tk_dv(Visa) : ten_he_thong không có trong thiet_bi_access"
                self.warning_onu_record.append(item)

                continue

            #
            ma_csht = self._thbi_access_service.thbi_access_dict_by_ten_hthong\
                        .get(ten_he_thong, {})\
                        .get(SC.K_MA_CSHT, "N/A")

            ttvt = str(
                        self._csht_ccl_service.csht_mdsd_items_ma_csht_dict\
                        .get(ma_csht, {})\
                        .get(SC.K_TEN_TTVT_TRAM_VT_NETX, "N/A")
                    )

            if self._valid_site_by_ttvt(ttvt) == None:
                LoggerUtil.get_logger().warning(
                    f"bc_ds_tk_dv : không xác định được Site : {item}"
                )

                bc_ds_tk_dv_olt_record.remove(item)

                item[SC.K_GHI_CHU] = "[loại] bc_ds_tk_dv(Visa) : không xác định được Site"
                self.warning_onu_record.append(item)

                continue

        ### Fillter VISA : trùng ten_hthong, slot, khác trang_thai -> lấy 1 record (ưu tiên "Hoạt động")
        bc_ds_tk_dv_olt_dict_by_ten_hthong_slot = defaultdict(list)
        for item in bc_ds_tk_dv_olt_record[:]:
            dict_key = (
                item.get(SC.K_TEN_HE_THONG),
                item.get(SC.K_FRAME),
                item.get(SC.K_SLOT),
                item.get(SC.K_PORT),
                item.get(SC.K_ONU),
            )

            bc_ds_tk_dv_olt_dict_by_ten_hthong_slot[dict_key].append(item)
        
        for k, item_list in bc_ds_tk_dv_olt_dict_by_ten_hthong_slot.items():
            if len(item_list) < 2:
                continue

            active_list = []
            not_active_list = []
            keep_item = {}

            for item in item_list:
                trg_thai: str = str(item.get(SC.K_TRANG_THAI, "")).strip().lower()
                if trg_thai == "hoạt động":
                    active_list.append(item)
                else:
                    not_active_list.append(item)

            if active_list:
                try:
                    active_list.sort(
                        key=lambda x:
                            (
                                safe_sort_date_time(x.get(SC.K_NGAY_NGHIEM_THU), "%d/%m/%Y %H:%M:%S"),
                            )
                    )
                except Exception as e:
                    LoggerUtil.get_logger().error(
                        f"Sort active_list failed : {active_list}"
                    )

                keep_item = active_list[-1]
            else:
                try:
                    not_active_list.sort(
                        key=lambda x:
                            (
                                safe_sort_date_time(x.get(SC.K_NGAY_NGHIEM_THU), "%d/%m/%Y %H:%M:%S"),
                            )
                    )
                except Exception as e:
                    LoggerUtil.get_logger().error(
                        f"Sort not_active_list failed : {not_active_list}"
                    )

                keep_item = not_active_list[-1]

            for item in item_list:
                # LoggerUtil.get_logger().warning(
                #     f"ds_tk_dv_hien_co : trùng tham_so, khác [trang_thai|user] : {item}"
                # )

                if item != keep_item:
                    bc_ds_tk_dv_olt_record.remove(item)
                    item[SC.K_GHI_CHU] = "[loại] ds_tk_dv_hien_co(Visa) : trùng tham_so, khác [trang_thai|user]"
                else:
                    item[SC.K_GHI_CHU] = "[*giữ] ds_tk_dv_hien_co(Visa) : trùng tham_so, khác [trang_thai|user]"

                self.warning_onu_record.append(item)

        ### Dict VISA by slot, user
        bc_ds_tk_dv_olt_dict_by_ten_hthong_slot_user = {}
        for item in bc_ds_tk_dv_olt_record[:]:
            dict_key = (
                item.get(SC.K_TEN_HE_THONG),
                item.get(SC.K_THBAO),
                item.get(SC.K_FRAME),
                item.get(SC.K_SLOT),
                item.get(SC.K_PORT),
                item.get(SC.K_ONU),
            )

            if dict_key not in bc_ds_tk_dv_olt_dict_by_ten_hthong_slot_user:
                bc_ds_tk_dv_olt_dict_by_ten_hthong_slot_user[dict_key] = item
            else:
                LoggerUtil.get_logger().error(
                    f"bc_ds_tk_dv_olt_dict_by_ten_hthong_slot_user [Must never occur] : trùng ten_hthong, user, onu : {item}"
                )

                bc_ds_tk_dv_olt_record.remove(bc_ds_tk_dv_olt_dict_by_ten_hthong_slot_user[dict_key])
                bc_ds_tk_dv_olt_dict_by_ten_hthong_slot_user[dict_key] = item

        # Fillter Visa: th_bao tren Card khong ton tai
        for item in bc_ds_tk_dv_olt_record[:]:
            ten_hthong = item.get(SC.K_TEN_HE_THONG, "N/A")
            slot = item.get(SC.K_SLOT, "N/A")

            card_by_slot_only = self._rp_card_access_service\
                .rp_card_access_dict_by_ten_hthong_slot_only\
                .get(
                    (ten_hthong, f'{slot}'), None
                )

            ### Card k tồn tại
            if not card_by_slot_only:
                bc_ds_tk_dv_olt_record.remove(item)

                item[SC.K_GHI_CHU] = "[loại] ds_tk_dv_hien_co(Visa) : th_bao trên Card không tồn tại"
                self.warning_onu_record.append(item)

                continue

            ### Vaid Serial
            last_serial_card = card_by_slot_only.get(SC.K_LAST_SERIAL, "N/A")
            last_valid_serial_card = card_by_slot_only.get(SC.K_LAST_VALID_SERIAL, "N/A")
            if last_serial_card in ["", None]:
                if last_valid_serial_card in ["", None]:
                    bc_ds_tk_dv_olt_record.remove(item)

                    item[SC.K_GHI_CHU] = "[loại] ds_tk_dv_hien_co(Visa) : th_bao trên Card chưa từng có Serial"
                    self.warning_onu_record.append(item)

                    continue
                else:
                    item[SC.K_GHI_CHU] = "[*giữ] ds_tk_dv_hien_co(Visa) : th_bao trên Card hiện tại không có Serial"
                    self.warning_onu_record.append(item)

        ############################# Fillter Chi tiet Onu
        for item in bc_chtiet_onu_record_all:
            ten_he_thong = item.get(SC.K_TEN_HE_THONG, "N/A")
            if ".olt." not in ten_he_thong.lower():
                continue

            item[SC.K_FRAME] = to_int(item.get(SC.K_FRAME), False)
            item[SC.K_SLOT] = to_int(item.get(SC.K_SLOT), False)
            item[SC.K_PORT] = to_int(item.get(SC.K_PORT), False)
            item[SC.K_ONU] = to_int(item.get(SC.K_ONU), False)

            item[SC.K_SRC] = "chtiet_onu"

            bc_chtiet_onu_olt_record.append(item)

        ### Fillter bc_chtiet_onu : trùng ten_hthong, slot, serial và user -> lấy 1 record
        bc_chtiet_onu_olt_dict_by_ten_hthong_slot_serial_user = {}
        for item in bc_chtiet_onu_olt_record[:]:
            #
            duplicated_counter = item.get(SC.K_DUPLICETED)
            if to_int(duplicated_counter) > 1:
                # LoggerUtil.get_logger().warning(
                #     f"bc_chi_tiet_onu: trùng ten_hthong, frame, slot, port, onu_idx, serial, th_bao : {item}"
                # )
                item[SC.K_GHI_CHU] = "[*giữ 1] bc_chi_tiet_onu : trùng ten_hthong, frame, slot, port, onu_idx, serial, th_bao"
                self.warning_onu_record.append(item)

            ten_he_thong = item.get(SC.K_TEN_HE_THONG)

            dict_key = (
                ten_he_thong,
                item.get(SC.K_FRAME),
                item.get(SC.K_SLOT),
                item.get(SC.K_PORT),
                item.get(SC.K_ONU),
                item.get(SC.K_SERIAL),
                item.get(SC.K_THBAO),
            )

            if dict_key not in bc_chtiet_onu_olt_dict_by_ten_hthong_slot_serial_user:
                bc_chtiet_onu_olt_dict_by_ten_hthong_slot_serial_user[dict_key] = item
            else:
                LoggerUtil.get_logger().error(
                    f"bc_chi_tiet_onu [Must never occur] : trùng ten_hthong, frame, slot, port, onu_idx, serial, th_bao : {item}"
                )
                bc_chtiet_onu_olt_record.remove(item)

                continue

            #
            if ten_he_thong not in self._thbi_access_service.thbi_access_dict_by_ten_hthong:
                LoggerUtil.get_logger().warning(
                    f"bc_chtiet_onu : ten_he_thong không có trong thiet_bi_access : {item}"
                )

                bc_chtiet_onu_olt_record.remove(item)

                item[SC.K_GHI_CHU] = "[loại] bc_chtiet_onu : ten_he_thong không có trong thiet_bi_access"
                self.warning_onu_record.append(item)

                continue

            #
            ma_csht = self._thbi_access_service.thbi_access_dict_by_ten_hthong\
                        .get(ten_he_thong, {})\
                        .get(SC.K_MA_CSHT, "N/A")

            ttvt = str(
                        self._csht_ccl_service.csht_mdsd_items_ma_csht_dict\
                        .get(ma_csht, {})\
                        .get(SC.K_TEN_TTVT_TRAM_VT_NETX, "N/A")
                    )

            if self._valid_site_by_ttvt(ttvt) == None:
                LoggerUtil.get_logger().warning(
                    f"bc_chi_tiet_onu : không xác định được Site : {item}"
                )

                bc_chtiet_onu_olt_record.remove(item)

                item[SC.K_GHI_CHU] = "[loại] bc_chtiet_onu : không xác định được Site"
                self.warning_onu_record.append(item)

                continue

        ### Fillter bc_chtiet_onu : Khác [User] thì user trên visa đang hoạt động (ưu tiên 1),
        ###tạm ngưng hay lock (ưu tiên 2)

        # Dict bc_chtiet_onu by slot
        bc_chtiet_onu_olt_dict_by_slot = defaultdict(list)
        for item in bc_chtiet_onu_olt_record[:]:
            dict_key = (
                item.get(SC.K_TEN_HE_THONG),
                item.get(SC.K_FRAME),
                item.get(SC.K_SLOT),
                item.get(SC.K_PORT),
                item.get(SC.K_ONU),
            )

            bc_chtiet_onu_olt_dict_by_slot[dict_key].append(item)

        for k, item_list in bc_chtiet_onu_olt_dict_by_slot.items():
            #
            if len(item_list) < 2:
                continue

            #
            def is_active(item):
                ### slot
                item_in_ds_tk_dv_olt_dict_by_ten_hthong_slot_user = \
                    bc_ds_tk_dv_olt_dict_by_ten_hthong_slot_user.get(
                        (
                            item.get(SC.K_TEN_HE_THONG),
                            item.get(SC.K_THBAO),
                            item.get(SC.K_FRAME),
                            item.get(SC.K_SLOT),
                            item.get(SC.K_PORT),
                            item.get(SC.K_ONU),
                        ),
                        {}
                    )

                trg_thai: str = str(
                    item_in_ds_tk_dv_olt_dict_by_ten_hthong_slot_user.get(SC.K_TRANG_THAI, "")
                ).strip().lower()

                if trg_thai == "hoạt động":
                    return True

                return False

            active_items = [item for item in item_list if is_active(item)]

            keep_item = None
            if active_items:
                keep_item = active_items[-1]
            else :
                keep_item = item_list[-1]

            for item in item_list:
                if item != keep_item:
                    bc_chtiet_onu_olt_record.remove(item)
                    item[SC.K_GHI_CHU] = "[loại] bc_chtiet_onu : trùng ten_hthong, frame, slot, port, onu, khác [SN|User]"
                else:
                    item[SC.K_GHI_CHU] = "[*giữ] bc_chtiet_onu : trùng ten_hthong, frame, slot, port, onu, khác [SN|User]"

                self.warning_onu_record.append(item)

            item_list = [keep_item]

        # Fillter chi_tiet_onu: th_bao tren Card khong ton tai
        for item in bc_chtiet_onu_olt_record[:]:
            ten_hthong = item.get(SC.K_TEN_HE_THONG, "N/A")
            slot = item.get(SC.K_SLOT, "N/A")

            card_by_slot_only = self._rp_card_access_service\
                    .rp_card_access_dict_by_ten_hthong_slot_only\
                    .get(
                        (ten_hthong, f'{slot}'), None
                    )

            ### Card k tồn tại
            if not card_by_slot_only:
                bc_chtiet_onu_olt_record.remove(item)

                item[SC.K_GHI_CHU] = "[loại] bc_chtiet_onu : th_bao trên Card không tồn tại"
                self.warning_onu_record.append(item)

                continue

            ### Vaid Serial
            last_serial_card = card_by_slot_only.get(SC.K_LAST_SERIAL, "N/A")
            last_valid_serial_card = card_by_slot_only.get(SC.K_LAST_VALID_SERIAL, "N/A")
            if last_serial_card in ["", None]:
                if last_valid_serial_card in ["", None]:
                    bc_chtiet_onu_olt_record.remove(item)

                    item[SC.K_GHI_CHU] = "[loại] bc_chtiet_onu : th_bao trên Card chưa từng có Serial"
                    self.warning_onu_record.append(item)

                    continue
                else:
                    item[SC.K_GHI_CHU] = "[*giữ] bc_chtiet_onu : th_bao trên Card hiện tại không có Serial"
                    self.warning_onu_record.append(item)

        ##### merge valid record in [VISA -> bc_chtiet_onu]
        _dict_by_ten_hthong = defaultdict(
            lambda: defaultdict(
                lambda: defaultdict(
                    lambda: defaultdict(
                        lambda: {
                            'onu_idx': set(),
                            SC.K_ONU: 0,
                        }
                    )
                )
            )
        )

        #
        bc_ds_tk_dv_olt_dict_by_ten_hthong_slot_filltered = {}

        for item in bc_ds_tk_dv_olt_record:
            ten_he_thong = item[SC.K_TEN_HE_THONG]
            frame = item[SC.K_FRAME]
            slot = item[SC.K_SLOT]
            port = item[SC.K_PORT]
            onu = item[SC.K_ONU]

            data = _dict_by_ten_hthong[ten_he_thong][frame][slot][port]

            if onu not in data['onu_idx']:
                data['onu_idx'].add(onu)
                data[SC.K_ONU] += 1

                self.all_valid_onu_record.append(item)
            else:
                pass

            #
            dict_key = (ten_he_thong, frame, slot, port, onu)
            if dict_key not in bc_ds_tk_dv_olt_dict_by_ten_hthong_slot_filltered:
                bc_ds_tk_dv_olt_dict_by_ten_hthong_slot_filltered[dict_key] = item
            else:
                LoggerUtil.get_logger().warning(
                    f"bc_ds_tk_dv_olt_dict_by_ten_hthong_slot_filltered trùng ten_hthong, onu, khac [th_bao|trang_thai] : {item}"
                )

        #
        bc_chi_tiet_onu_dict_by_ten_hthong_slot_filltered = {}

        for item in bc_chtiet_onu_olt_record:
            ten_he_thong = item[SC.K_TEN_HE_THONG]
            frame = item[SC.K_FRAME]
            slot = item[SC.K_SLOT]
            port = item[SC.K_PORT]
            onu = item[SC.K_ONU]

            data = _dict_by_ten_hthong[ten_he_thong][frame][slot][port]

            if onu not in data['onu_idx']:
                data['onu_idx'].add(onu)
                data[SC.K_ONU] += 1
                #

                self.all_valid_onu_record.append(item)
            else:
                pass

            #
            dict_key = (ten_he_thong, frame, slot, port, onu)
            if dict_key not in bc_chi_tiet_onu_dict_by_ten_hthong_slot_filltered:
                bc_chi_tiet_onu_dict_by_ten_hthong_slot_filltered[dict_key] = item
            else:
                LoggerUtil.get_logger().warning(
                    f"bc_chi_tiet_onu_dict_by_ten_hthong_slot_filltered trùng ten_hthong, onu, khac [th_bao] : {item}"
                )

        #
        self.bc_chtiet_onu_dict_by_ten_hthong = _dict_by_ten_hthong

        # Fill more info for record
        for item in chain(self.warning_onu_record, self.all_valid_onu_record):
            ten_he_thong = item[SC.K_TEN_HE_THONG]
            frame = item[SC.K_FRAME]
            slot = item[SC.K_SLOT]
            port = item[SC.K_PORT]
            onu = item[SC.K_ONU]

            src = item[SC.K_SRC]

            match src:
                case "visa":
                    chi_tiet_onu_item = bc_chi_tiet_onu_dict_by_ten_hthong_slot_filltered.get(
                        (ten_he_thong, frame, slot, port, onu), {}
                    )
                    if chi_tiet_onu_item:
                        item[SC.K_SERIAL] = chi_tiet_onu_item.get(SC.K_SERIAL, "")
                        item[SC.K_LOAI_ONU] = chi_tiet_onu_item.get(SC.K_LOAI_ONU, "")
                        item[SC.K_TEN_ONU] = chi_tiet_onu_item.get(SC.K_TEN_ONU, "")

                case "chtiet_onu":
                    bc_ds_tk_dv_olt_item = bc_ds_tk_dv_olt_dict_by_ten_hthong_slot_filltered.get(
                        (ten_he_thong, frame, slot, port, onu), {}
                    )
                    if bc_ds_tk_dv_olt_item:
                        item[SC.K_KH_HANG] = bc_ds_tk_dv_olt_item.get(SC.K_KH_HANG, "")
                        item[SC.K_DIA_CHI] = bc_ds_tk_dv_olt_item.get(SC.K_DIA_CHI, "")
                        item[SC.K_TRANG_THAI] = bc_ds_tk_dv_olt_item.get(SC.K_TRANG_THAI, "")
                        item[SC.K_THAM_SO] = bc_ds_tk_dv_olt_item.get(SC.K_THAM_SO, "")
                        item[SC.K_DVU] = bc_ds_tk_dv_olt_item.get(SC.K_DVU, "")

                case _:
                    LoggerUtil.get_logger().error(
                        f"{self.__class__.__name__} src: {src} not identify"
                    )