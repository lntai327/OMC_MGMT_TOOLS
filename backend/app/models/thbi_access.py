from typing import Optional
from sqlalchemy import BigInteger, String, Text, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, TimestampMixin

from app.constant import constant as SC


class ThbiAccessMd(Base, TimestampMixin):
    __tablename__ = "thbi_access"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ma_csht: Mapped[Optional[str]] = mapped_column(String(500), nullable=True, index=True)
    ten_he_thong: Mapped[Optional[str]] = mapped_column(String(500), nullable=True, index=True)
    chuc_nang: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    ip: Mapped[Optional[str]] = mapped_column(String(500), nullable=True, index=True)
    dong: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    __table_args__ = (
        Index("idx_thbi_access_multi_search", "ma_csht", "ten_he_thong", "chuc_nang"),
    )

    def to_dict(self) -> dict:
        return {
            SC.K_ID: self.id,
            SC.K_MA_CSHT: self.ma_csht,
            SC.K_TEN_HE_THONG: self.ten_he_thong,
            SC.K_CHUC_NANG: self.chuc_nang,
            SC.K_IP: self.ip,
            SC.K_DONG: self.dong,
        }

