from datetime import datetime, date, timedelta, timezone

from share.constant import constant as SC

class TimeUtil:
    # UTC+7
    VN_TZ = timezone(timedelta(hours=7))

    def __init__(self):
        pass

    def get_current_time_str(self):
        return datetime.now(self.VN_TZ).strftime(SC.K_DATETIME_FORMAT)

    def get_detail_current_time_str(self) -> str:
        return datetime.now(self.VN_TZ).strftime("%H:%M:%S %d/%m/%Y")

    def get_rp_time_by_weeknumber(
            self, weeknumber: int = None, month: int = None, year: int = None):
        now = datetime.now(self.VN_TZ)
        if year is None:
            year = now.year
        if month is None:
            month = now.month

        # weekday(): Monday=0 ... Sunday=6 -> Friday=4
        jan1 = date(year, 1, 1)
        days_to_1st_fri = (4 - jan1.weekday()) % 7
        first_friday = jan1 + timedelta(days=days_to_1st_fri)

        if weeknumber is None:
            today = now.date()
            delta_days = (today - first_friday).days

            if delta_days < 0:
                weeknumber = 1
            else:
                weeknumber = (delta_days // 7) + 1

        if weeknumber < 1:
            raise ValueError("weeknumber must be >= 1")

        rp_time_from_date = first_friday + timedelta(weeks=weeknumber - 1)
        rp_time_to_date = rp_time_from_date + timedelta(days=6)
        
        rp_time_from = rp_time_from_date.strftime(SC.K_DATETIME_FORMAT)
        rp_time_to = rp_time_to_date.strftime(SC.K_DATETIME_FORMAT)

        return rp_time_from, rp_time_to