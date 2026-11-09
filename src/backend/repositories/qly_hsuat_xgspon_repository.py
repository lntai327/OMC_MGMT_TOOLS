from share.util.logger_util import LoggerUtil
from typing import List, Optional

from backend.db.database import Database
from backend.models.qly_hsuat_xgspon import QlyHsuatXgspon
from share.constant import constant as SC


class QlyHsuatRepository:
    """Data access layer."""

    def __init__(self) -> None:
        self._db_factory = Database()

    def get_all(self) -> List[QlyHsuatXgspon]:
        with self._db_factory.get_session() as session:
            return session.query(QlyHsuatXgspon).all()

    def get(self, ten_he_thong: str) -> Optional[QlyHsuatXgspon]:
        with self._db_factory.get_session() as session:
            return session.query(QlyHsuatXgspon) \
                .filter(QlyHsuatXgspon.ten_he_thong == ten_he_thong).first()

    def create(self, data: dict) -> QlyHsuatXgspon:
        LoggerUtil.get_logger().info(f"QlyHsuat Xgspon create: {data}")
        with self._db_factory.get_session() as session:
            record = QlyHsuatXgspon(**data)
            session.add(record)
            session.flush()
            session.refresh(record)
            session.expunge(record)
            return record

    def update(self, ten_he_thong: str, data: dict) -> Optional[QlyHsuatXgspon]:
        LoggerUtil.get_logger().info(f"QlyHsuat Xgspon update: {data}")
        with self._db_factory.get_session() as session:
            record = session.query(QlyHsuatXgspon) \
                .filter(QlyHsuatXgspon.ten_he_thong == ten_he_thong).first()
            if record is None:
                return None
            for key, value in data.items():
                setattr(record, key, value)
            session.flush()
            session.refresh(record)
            session.expunge(record)
            return record

    def delete(self, ten_he_thong: str) -> bool:
        LoggerUtil.get_logger().info(f"QlyHsuat Xgspon delete: {ten_he_thong}")
        with self._db_factory.get_session() as session:
            record = session.query(QlyHsuatXgspon) \
                .filter(QlyHsuatXgspon.ten_he_thong == ten_he_thong).first()
            if record is None:
                return False
            session.delete(record)
            return True
