from typing import List, Optional, Tuple
from sqlalchemy import func, or_, select, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.megawan_metronet import MegawanMetronetMd
from app.schemas.megawan_metronet import MegawanFilterParams
from app.repositories.base_repo import BaseRepository
from app.repositories.thbi_access_repo import thbi_access_repo
from app.core.timezone import now_vietnam


class MegawanMetronetRepo(BaseRepository[MegawanMetronetMd]):
    def __init__(self):
        super().__init__(MegawanMetronetMd)

    def _build_filter_conditions(self, filters: MegawanFilterParams) -> list:
        conditions = []

        if filters.loai_hinh_tb:
            conditions.append(MegawanMetronetMd.loai_hinh_tb.ilike(f"%{filters.loai_hinh_tb.strip()}%"))
        if filters.ten_th_bao:
            conditions.append(MegawanMetronetMd.ten_th_bao.ilike(f"%{filters.ten_th_bao.strip()}%"))
        if filters.dia_chi:
            conditions.append(MegawanMetronetMd.dia_chi.ilike(f"%{filters.dia_chi.strip()}%"))
        if filters.loai_kenh:
            conditions.append(MegawanMetronetMd.loai_kenh.ilike(f"%{filters.loai_kenh.strip()}%"))
        if filters.svlan_cvlan:
            conditions.append(MegawanMetronetMd.svlan_cvlan.ilike(f"%{filters.svlan_cvlan.strip()}%"))
        if filters.ten_thbi:
            conditions.append(MegawanMetronetMd.ten_thbi.ilike(f"%{filters.ten_thbi.strip()}%"))

        if filters.all_search and filters.all_search.strip():
            kw = f"%{filters.all_search.strip()}%"
            conditions.append(
                or_(
                    MegawanMetronetMd.last_update.ilike(kw),
                    MegawanMetronetMd.ma_tb.ilike(kw),
                    MegawanMetronetMd.ma_lt_ma_tb_sub.ilike(kw),
                    MegawanMetronetMd.ten_th_bao.ilike(kw),
                    MegawanMetronetMd.dia_chi.ilike(kw),
                    MegawanMetronetMd.diem_cuoi.ilike(kw),
                    MegawanMetronetMd.svlan_cvlan.ilike(kw),
                    MegawanMetronetMd.ten_thbi.ilike(kw),
                    MegawanMetronetMd.ip_thbi.ilike(kw),
                    MegawanMetronetMd.port_thbi.ilike(kw),
                    MegawanMetronetMd.upe.ilike(kw),
                    MegawanMetronetMd.ip_kh.ilike(kw),
                    MegawanMetronetMd.ip_gw.ilike(kw),
                    MegawanMetronetMd.loai_hinh_tb.ilike(kw),
                    MegawanMetronetMd.toc_do.ilike(kw),
                    MegawanMetronetMd.loai_kenh.ilike(kw),
                    MegawanMetronetMd.trang_thai.ilike(kw),
                    MegawanMetronetMd.cap_odf.ilike(kw),
                    MegawanMetronetMd.ghi_chu.ilike(kw),
                )
            )

        return conditions

    async def get_filtered_records(
        self,
        session: AsyncSession,
        filters: MegawanFilterParams,
        skip: int = 0,
        limit: int = 20,
        sort_by: Optional[str] = None,
        sort_desc: bool = False,
    ) -> Tuple[List[MegawanMetronetMd], int]:
        conditions = self._build_filter_conditions(filters)

        # Count total
        count_stmt = select(func.count()).select_from(MegawanMetronetMd)
        if conditions:
            count_stmt = count_stmt.where(*conditions)
        total_res = await session.execute(count_stmt)
        total = total_res.scalar_one() or 0

        # Data query
        query = select(MegawanMetronetMd)
        if conditions:
            query = query.where(*conditions)

        # Sorting
        if sort_by and hasattr(MegawanMetronetMd, sort_by):
            sort_col = getattr(MegawanMetronetMd, sort_by)
            query = query.order_by(desc(sort_col) if sort_desc else asc(sort_col))
        else:
            query = query.order_by(desc(MegawanMetronetMd.id))

        query = query.offset(skip).limit(limit)
        result = await session.execute(query)
        items = list(result.scalars().all())

        return items, total

    async def get_all_by_filters_stream(
        self,
        session: AsyncSession,
        filters: MegawanFilterParams,
    ) -> List[MegawanMetronetMd]:
        """Fetch all matching records for report export."""
        conditions = self._build_filter_conditions(filters)
        query = select(MegawanMetronetMd)
        if conditions:
            query = query.where(*conditions)
        query = query.order_by(asc(MegawanMetronetMd.id))
        result = await session.execute(query)
        return list(result.scalars().all())

    async def bulk_create(
        self,
        session: AsyncSession,
        records: List[dict]
    ) -> int:
        """Bulk insert records for fast Excel import."""
        if not records:
            return 0
        valid_cols = {c.name for c in MegawanMetronetMd.__table__.columns if c.name != "id"}
        clean_records = [
            {k: v for k, v in rec.items() if k in valid_cols}
            for rec in records
        ]
        objects = [MegawanMetronetMd(**rec) for rec in clean_records if rec]
        session.add_all(objects)
        await session.flush()
        return len(objects)

    async def upsert_by_id(
        self,
        session: AsyncSession,
        record_dict: dict,
    ) -> str:
        """Insert or update a record based on the 'id' field.

        - If id is a valid integer and a matching row exists → update it.
        - Otherwise → insert a new row (auto-increment id).

        Returns 'updated' or 'inserted'.
        """
        valid_cols = {c.name for c in MegawanMetronetMd.__table__.columns}
        # Non-writable columns during update (preserve original created_at)
        skip_on_update = {"id", "created_at"}

        raw_id = record_dict.get("id")
        if raw_id is not None and str(raw_id).strip() != "":
            try:
                record_id = int(raw_id)
                existing = await session.get(MegawanMetronetMd, record_id)
                if existing:
                    for k, v in record_dict.items():
                        if k not in skip_on_update and k in valid_cols:
                            setattr(existing, k, v)
                    existing.updated_at = now_vietnam()
                    await session.flush()
                    return "updated"
            except (ValueError, TypeError):
                pass  # id không hợp lệ → fall-through to insert

        # Insert new (never write id — let auto-increment handle it)
        insert_cols = {k: v for k, v in record_dict.items() if k in valid_cols and k != "id"}
        obj = MegawanMetronetMd(**insert_cols)
        session.add(obj)
        await session.flush()
        return "inserted"

    async def delete_by_id(
        self,
        session: AsyncSession,
        record_id,
    ) -> bool:
        """Delete a record by its primary key id.

        Returns True if deleted, False if not found or id invalid.
        """
        if record_id is None or str(record_id).strip() == "":
            return False
        try:
            pk = int(record_id)
            obj = await session.get(MegawanMetronetMd, pk)
            if obj:
                await session.delete(obj)
                await session.flush()
                return True
        except (ValueError, TypeError):
            pass
        return False


    async def get_distinct_field_options(self, session: AsyncSession) -> dict[str, List[str]]:
        cols = {
            "loai_hinh_tb": MegawanMetronetMd.loai_hinh_tb,
            "loai_kenh": MegawanMetronetMd.loai_kenh,
            "trang_thai": MegawanMetronetMd.trang_thai,
        }
        result: dict[str, List[str]] = {}
        for key, col in cols.items():
            query = (
                select(col)
                .where(col.isnot(None), col != "")
                .distinct()
                .order_by(col)
            )
            rows = await session.execute(query)
            distinct_values = sorted(list({str(r[0]).strip() for r in rows.all() if r[0] and str(r[0]).strip()}))
            result[key] = distinct_values

        #
        result["ten_thbi"] = await thbi_access_repo.get_distinct_gpon_devices(session)

        return result


megawan_metronet_repo = MegawanMetronetRepo()

