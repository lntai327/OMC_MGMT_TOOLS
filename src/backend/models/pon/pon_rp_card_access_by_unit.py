from sqlalchemy import Column, Integer, Unicode

from backend.db.database import Base
from share.util.time_util import TimeUtil
from share.constant import constant as SC

class RpCardAccessMd(Base):
    """ORM model mapping to table."""

    __tablename__ = "pon_rp_card_access_by_unit"
    __table_args__ = {"implicit_returning": False}

    id = Column(Integer, primary_key=True, autoincrement=True)
    last_update = Column(
        Unicode(100), default=TimeUtil().get_detail_current_time_str
    )
    ten_he_thong = Column(Unicode(100), nullable=False)
    slot = Column(Unicode(50))
    ten_card = Column(Unicode(100))
    last_serial = Column(Unicode(100))
    dong = Column(Unicode(100))
    hang_sx = Column(Unicode(100))
    last_valid_serial = Column(Unicode(100))

    def __repr__(self) -> str:
        return f"<RpCardAccessMd(id={self.id}, ten_he_thong={self.ten_he_thong!r})>"

    def to_dict(self) -> dict:
        return {
            SC.K_TEN_HE_THONG: self.ten_he_thong,
            SC.K_SLOT: self.slot,
            SC.K_TEN_CARD: self.ten_card,
            SC.K_LAST_SERIAL: self.last_serial,
            SC.K_DONG: self.dong,
            SC.K_HANG_SX: self.hang_sx,
            SC.K_LAST_VALID_SERIAL: self.last_valid_serial,
        }

    def load(self, item_dic) -> 'RpCardAccessMd':
        self.ten_he_thong = item_dic.get('Tên hệ thống', 'N/A')
        self.slot = item_dic.get('Slot', 'N/A')
        self.ten_card = item_dic.get('Tên card', 'N/A')
        self.last_serial = item_dic.get('Số Serial', 'N/A')
        self.dong = item_dic.get('Dòng', 'N/A')
        self.hang_sx = item_dic.get('Hãng sản xuất', 'N/A')

        return self
