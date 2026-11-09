from datetime import datetime

from share.util.logger_util import LoggerUtil
from share.constant import type as ST

def to_int(value, force: bool = True):
    try:
        return int(value)
    except (TypeError, ValueError):
        if force:
            return 0
        else:
            return value
        
def to_float(value, force: bool = True):
    try:
        return float(value)
    except (TypeError, ValueError):
        if force:
            return 0
        else:
            return value
        
def normalize_str_input_value(value) -> str:
    return "" if value is None else str(value).strip()

def safe_sort_value(value):
    if value is None:
        return (0, "")
    return (1, value)

def safe_sort_str(value):
    if value is None:
        return (0, "")
    return (1, str(value))

def safe_sort_num(value):
    if not isinstance(value, (int, float)):
        return (0, float("-inf"))
    return (1, float(value))

def safe_sort_date_time(date_time: str, format: str):
    try:
        return (
            1,
            datetime.strptime(
                str(date_time).strip(),
                format,
            ),
        )
    except Exception as e:
        LoggerUtil.get_logger().error(
            f"_sort_date_time failed at {date_time} due to {e}"
        )
        return (0, datetime.min)
    
def to_site_ui(value: str):
    match str(value).lower():
        case ST.Site.DONG.value:
            return "Đông"
        case ST.Site.TAY.value:
            return "Tây"
        case ST.Site.ALL_SITE.value:
            return "Tất Cả Site"
        case _:
            return None