import os
from typing import List, Optional
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from backend.repositories.megawan_metronet.megawan_metronet_repo import MegawanService
from backend.constant import type as T
from share.constant import constant as SC
from share.util.logger_util import LoggerUtil
from share.util.time_util import TimeUtil
from share.util.explorer_util import ExplorerUtil

class MegawanMetronetService():
    def __init__(self) -> None:
        self._megawan_service = MegawanService()

    def load(self) -> List[dict]:
        self._megawan_service.load()

        all_record = self._megawan_service.all_record

        return all_record

    def create_record(self, data: dict) -> dict:
        ret_dict = self._megawan_service.create_record(data)

        return ret_dict

    def update_record(self, record_id: int, data: dict) -> Optional[dict]:
        ret_dict = self._megawan_service.update_record(record_id, data)

        return ret_dict

    def delete_record(self, record_id: int) -> bool:
        ret = self._megawan_service.delete_record(record_id)

        return ret

    def export_to_excel(self, records: List[dict], folder_path: str) -> str:
        if not os.path.exists(folder_path):
            os.makedirs(folder_path, exist_ok=True)

        excel_output_file_name = (
            f"Megawan Metronet"
            f"_{TimeUtil().get_detail_current_time_str().replace(':', '').replace('/', '') or ''}"
            f".xlsx"
        )

        excel_output_full_path = os.path.join(folder_path, excel_output_file_name)

        excel_output_template_path = \
            ExplorerUtil().get_output_template_file_path(
                f"Megawan Metronet-template.xlsx"
            )

        ret = ExplorerUtil().cp_to_folder(
            excel_output_template_path,
            os.path.dirname(excel_output_full_path),
            os.path.basename(excel_output_full_path),
        )

        if ret is None or ret != excel_output_full_path:
            LoggerUtil.get_logger().error(
                f"Megawan_Metronet export_to_excel failed create ret_path = {ret}, filepath = {excel_output_full_path}"
            )
            raise RuntimeError

        HEADER_FIELDS = [
            SC.K_STT,
            SC.K_MA_TB,
            SC.K_MA_LT_MA_TB_SUB,
            SC.K_TEN_TH_BAO,
            SC.K_DIA_CHI,
            SC.K_ID,
            SC.K_DIEM_CUOI,
            SC.K_IP_SRC,
            SC.K_IP_DES,
            SC.K_SVLAN_CVLAN,
            SC.K_CAP_ADSL,
            SC.K_CAP_ODF,
            SC.K_LAST_UPDATE,
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

        wb = openpyxl.load_workbook(excel_output_full_path)
        ws = wb["data"]

        for row_idx, item in enumerate(records, start=2):
            for col_idx, key in enumerate(HEADER_FIELDS, start=1):
                value = item.get(key, "N/A")
                cell = ws.cell(row=row_idx, column=col_idx, value=value)
                cell.border = T.EX_FORMAT_THIN_BORDER

        # # Auto-fit column widths
        # for col in ws.columns:
        #     max_len = 0
        #     col_letter = get_column_letter(col[0].column)
        #     for cell in col:
        #         val = str(cell.value or "")
        #         if len(val) > max_len:
        #             max_len = len(val)
        #     ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

        # # Freeze header row
        # ws.freeze_panes = "A2"

        wb.save(excel_output_full_path)
        wb.close()
        LoggerUtil.get_logger().info(
            f"MegawanMetronetService exported {len(records)} records to {excel_output_full_path}"
        )

        return excel_output_full_path
