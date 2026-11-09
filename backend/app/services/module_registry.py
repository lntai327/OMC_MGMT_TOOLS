from typing import Dict, Any, Type
from app.repositories.megawan_metronet_repo import megawan_metronet_repo
from app.schemas.megawan_metronet import MegawanFilterParams
from app.services.excel_streamer import ExcelStreamer

# Module Registry liên kết giữa file_key và Repository / Filter / Export tương ứng
MODULE_REGISTRY: Dict[str, Dict[str, Any]] = {
    "megawan_metronet": {
        "repo": megawan_metronet_repo,
        "filter_schema": MegawanFilterParams,
        "export_func": ExcelStreamer.export_megawan,
        "template_name": "Megawan Metronet-template.xlsx",
        "export_filename_prefix": "Megawan_Metronet",
        "header_row_range": 1,
    },
    # Sau này bổ sung thêm các module khác chỉ cần khai báo tại đây:
    # "excel_thbi_access": { ... },
    # "excel_bc_bts": { ... },
}


def get_module_config(file_key: str) -> Dict[str, Any]:
    """Lấy cấu hình phân hệ theo file_key, báo lỗi nếu file_key chưa được đăng ký."""
    if file_key not in MODULE_REGISTRY:
        raise ValueError(
            f"file_key '{file_key}' chưa được đăng ký trong MODULE_REGISTRY. "
            f"Các key hiện có: {list(MODULE_REGISTRY.keys())}"
        )
    return MODULE_REGISTRY[file_key]

