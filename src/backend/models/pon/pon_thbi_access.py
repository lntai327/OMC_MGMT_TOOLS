from sqlalchemy import Column, Integer, Unicode

from backend.db.database import Base
from share.util.time_util import TimeUtil
from share.constant import constant as SC

class ThbiAccessMd(Base):
    """ORM model mapping to table."""

    __tablename__ = "pon_thbi_access"
    __table_args__ = {"implicit_returning": False}

    id = Column(Integer, primary_key=True, autoincrement=True)
    last_update = Column(
        Unicode(100), default=TimeUtil().get_detail_current_time_str
    )
    ma_csht = Column(Unicode(100))
    ten_he_thong = Column(Unicode(100), nullable=False)
    chuc_nang = Column(Unicode(100))
    ip: Column[str] = Column(Unicode(100))
    dong = Column(Unicode(100))

    def __repr__(self) -> str:
        return f"<ThbiAccessMd(id={self.id}, ten_he_thong={self.ten_he_thong!r})>"

    def to_dict(self) -> dict:
        return {
            SC.K_MA_CSHT: self.ma_csht,
            SC.K_TEN_HE_THONG: self.ten_he_thong,
            SC.K_CHUC_NANG: self.chuc_nang,
            SC.K_IP: self.ip,
            SC.K_DONG: self.dong,
        }

    def load(self, item_dic) -> 'ThbiAccessMd':
        self.ma_csht = item_dic.get('Mã nhà trạm', 'N/A')
        self.ten_he_thong = item_dic.get('Tên hệ thống', 'N/A')
        self.chuc_nang = item_dic.get('Chức năng', 'N/A')
        self.ip = item_dic.get('Địa chỉ IP', 'N/A')
        self.dong = item_dic.get('Dòng', 'N/A')

        return self
