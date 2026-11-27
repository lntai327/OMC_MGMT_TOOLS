from typing import Dict, Any, Type
from app.constant import constant as SC
from app.repositories.megawan_metronet_repo import megawan_metronet_repo
from app.repositories.thbi_access_repo import thbi_access_repo
from app.schemas.megawan_metronet import MegawanFilterParams
from app.services.excel_streamer import ExcelStreamer

# Module Registry match file_key to Repository / Filter / Export
MODULE_REGISTRY: Dict[str, Dict[str, Any]] = {
    SC.K_EXCEL_MEGAWAN: {
        "repo": megawan_metronet_repo,
        "header_row_range": 1,
        "import_mode": "action",
        "filter_schema": MegawanFilterParams,
        "export_func": ExcelStreamer.export_megawan,
        "template_name": "Megawan Metronet-template.xlsx",
        "export_filename_prefix": "Megawan_Metronet",
    },
    SC.K_EXCEL_THBI_ACCESS: {
        "repo": thbi_access_repo,
        "header_row_range": 1,
        "import_mode": "sync_by_key",
        "key_field": SC.K_TEN_HE_THONG,
    },
}


def get_module_config(file_key: str) -> Dict[str, Any]:
    if file_key not in MODULE_REGISTRY:
        raise ValueError(
            f"file_key '{file_key}' not registered in MODULE_REGISTRY. "
        )
    return MODULE_REGISTRY[file_key]

