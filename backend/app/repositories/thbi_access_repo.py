from collections import defaultdict
from typing import Any, Dict, List
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.thbi_access import ThbiAccessMd
from app.repositories.base_repo import BaseRepository
from app.core.timezone import now_vietnam


class ThbiAccessRepo(BaseRepository[ThbiAccessMd]):
    def __init__(self):
        super().__init__(ThbiAccessMd)

    async def get_distinct_gpon_devices(self, session: AsyncSession) -> List[str]:
        query = (
            select(ThbiAccessMd.ten_he_thong)
            .where(
                ThbiAccessMd.ten_he_thong.isnot(None),
                ThbiAccessMd.ten_he_thong != "",
                func.lower(func.trim(ThbiAccessMd.chuc_nang)) == "gpon",
            )
            .distinct()
            .order_by(ThbiAccessMd.ten_he_thong)
        )
        rows = await session.execute(query)
        return sorted(list({str(r[0]).strip() for r in rows.all() if r[0] and str(r[0]).strip()}))

    async def sync_records_by_ten_he_thong(
        self,
        session: AsyncSession,
        excel_records: Dict[str, Dict[str, Any]],
    ) -> Dict[str, int]:
        # 1. Lấy tất cả bản ghi hiện có trong DB
        query = select(ThbiAccessMd)
        res = await session.execute(query)
        db_items = list(res.scalars().all())

        # Nhóm theo ten_he_thong chuẩn hóa
        db_map: Dict[str, List[ThbiAccessMd]] = defaultdict(list)
        for item in db_items:
            key = str(item.ten_he_thong).strip() if item.ten_he_thong else ""
            db_map[key].append(item)

        excel_keys = set(excel_records.keys())
        now = now_vietnam()

        inserted_count = 0
        updated_count = 0
        deleted_count = 0

        # 2. Xử lý Thêm mới hoặc Cập nhật
        for key, new_data in excel_records.items():
            if key in db_map and db_map[key]:
                # Có trong Excel và đồng thời có trong DB -> Cập nhật vào DB
                existing = db_map[key][0]
                existing.ma_csht = new_data.get("ma_csht")
                existing.chuc_nang = new_data.get("chuc_nang")
                existing.ip = new_data.get("ip")
                existing.dong = new_data.get("dong")
                existing.updated_at = now
                updated_count += 1

                # Nếu trong DB trước đó có nhiều hơn 1 record trùng key này, xóa các record thừa
                for extra in db_map[key][1:]:
                    await session.delete(extra)
                    deleted_count += 1
            else:
                # Có trong Excel nhưng không có trong DB -> Thêm mới vào DB
                new_obj = ThbiAccessMd(
                    ma_csht=new_data.get("ma_csht"),
                    ten_he_thong=new_data.get("ten_he_thong"),
                    chuc_nang=new_data.get("chuc_nang"),
                    ip=new_data.get("ip"),
                    dong=new_data.get("dong"),
                    created_at=now,
                    updated_at=now,
                )
                session.add(new_obj)
                inserted_count += 1

        # 3. Xử lý Xóa: Không có trong file Excel nhưng có trong DB -> Xóa khỏi DB
        for db_key, items in db_map.items():
            if db_key not in excel_keys:
                for item in items:
                    await session.delete(item)
                    deleted_count += 1

        await session.flush()

        return {
            "inserted": inserted_count,
            "updated": updated_count,
            "deleted": deleted_count,
        }


thbi_access_repo = ThbiAccessRepo()
