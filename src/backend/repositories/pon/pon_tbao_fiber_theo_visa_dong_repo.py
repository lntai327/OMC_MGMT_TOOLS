from typing import List

from backend.models.pon.pon_tbao_fiber_theo_visa_dong_md import TbaoFiberVisaDongMd
from backend.repositories.base_repo import BaseRepository
from backend.repositories.base_service import BaseService
from backend.util.ex_handle_util import ExcelHandleUtil
from share.constant import constant as SC
from share.util.convert import to_int
from share.util.dynamic_info_util import DynamicInfoUtil
from share.util.explorer_util import ExplorerUtil
from share.util.logger_util import LoggerUtil

class BcDsDvuHienCoRepo(BaseRepository[TbaoFiberVisaDongMd]):
    """Data access layer."""

    def __init__(self) -> None:
        super().__init__(TbaoFiberVisaDongMd)

    def _get_unique_key_column_dict(self) -> dict:
        return {
            TbaoFiberVisaDongMd.t_khoan: SC.K_T_KHOAN,
            TbaoFiberVisaDongMd.tham_so: SC.K_THAM_SO,
        }

class TbaoFiberVisaDongService(BaseService):
    """Business logic layer."""

    _model_class = TbaoFiberVisaDongMd

    def __init__(self) -> None:
        self._repo = BcDsDvuHienCoRepo()
        self.all_record: List[dict] = []

    def _get_excel_config(self):
        return (SC.K_EXCEL_TBAO_FIBER_VISA_DONG, SC.K_SHEET_DATA, 1)

    def _get_unique_record_key(self) -> List:
        return [
            SC.K_T_KHOAN,
            SC.K_TRANG_THAI,
            SC.K_THAM_SO,
        ]

    def _get_must_valid_record_key(self) -> List:
        return [
            SC.K_THAM_SO,
        ]

    def _get_data_payload_key(self) -> List:
        return [
            SC.K_T_KHOAN,
            SC.K_KH_HANG,
            SC.K_DIA_CHI,
            SC.K_NGAY_NGHIEM_THU,
            SC.K_TRANG_THAI,
            SC.K_IP,
            SC.K_THAM_SO,
            SC.K_DVU,
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
        ret: List[TbaoFiberVisaDongMd] = self._repo.get_all()

        all_record: List[dict] = [record.to_dict() for record in ret]

        self.all_record = all_record