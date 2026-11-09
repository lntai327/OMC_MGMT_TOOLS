from sqlalchemy import Column, Integer, Unicode

from backend.db.database import Base
from share.util.time_util import TimeUtil
from share.constant import constant as SC

class RpTransAccessMd(Base):
    """ORM model mapping to table."""

    __tablename__ = "pon_rp_trans_access_by_unit"
    __table_args__ = {"implicit_returning": False}

    id = Column(Integer, primary_key=True, autoincrement=True)
    last_update = Column(
        Unicode(100), default=TimeUtil().get_detail_current_time_str
    )
    ten_he_thong = Column(Unicode(100), nullable=False)
    model = Column(Unicode(100))
    serial = Column(Unicode(100))
    vi_tri = Column(Unicode(100))

    def __repr__(self) -> str:
        return f"<RpTransAccessMd(id={self.id}, ten_he_thong={self.ten_he_thong!r})>"

    def to_dict(self) -> dict:
        return {
            SC.K_TEN_HE_THONG: self.ten_he_thong,
            SC.K_MODEL: self.model,
            SC.K_SERIAL: self.serial,
            SC.K_VI_TRI: self.vi_tri,
        }

    def load(self, item_dic) -> 'RpTransAccessMd':
        self.ten_he_thong = item_dic.get('Tên hệ thống', 'N/A')
        self.model = item_dic.get('Model P/N', 'N/A')
        self.serial = item_dic.get('Số Serial', 'N/A')
        self.vi_tri = item_dic.get('Vị trí lắp', 'N/A')

        return self
