from sqlalchemy import Column, Integer, Unicode

from backend.db.database import Base
from share.util.time_util import TimeUtil
from share.constant import constant as SC

class TghopThbiGponTrenMangMd(Base):
    """ORM model mapping to table."""

    __tablename__ = "pon_tghop_thbi_gpon_tren_mang"
    __table_args__ = {"implicit_returning": False}

    id = Column(Integer, primary_key=True, autoincrement=True)
    last_update = Column(Unicode(100), default=TimeUtil().get_detail_current_time_str)
    ten_he_thong = Column(Unicode(100), nullable=False)
    ip = Column(Unicode(100))
    dia_diem = Column(Unicode(255))
    loai = Column(Unicode(100))
    so_card_dk = Column(Unicode(50))
    cong_ge = Column(Unicode(50))
    cong_10ge = Column(Unicode(50))
    lt4: Column[str] = Column(Unicode(50))
    lt8 = Column(Unicode(50))
    lt16 = Column(Unicode(50))
    su_dung_1 = Column(Unicode(50))
    su_dung_2 = Column(Unicode(50))

    def __repr__(self) -> str:
        return f"<TghopThbiGponTrenMang(id={self.id}, name={self.ten_he_thong!r})>"

    def to_dict(self) -> dict:
        return {
            SC.K_TEN_HE_THONG: self.ten_he_thong,
            SC.K_IP: self.ip,
            SC.K_DIA_DIEM: self.dia_diem,
            SC.K_LOAI: self.loai,
            SC.K_SO_CARD_DK: self.so_card_dk,
            SC.K_CONG_GE: self.cong_ge,
            SC.K_CONG_10GE: self.cong_10ge,
            SC.K_LT4: self.lt4,
            SC.K_LT8: self.lt8,
            SC.K_LT16: self.lt16,
            SC.K_SU_DUNG_1: self.su_dung_1,
            SC.K_SU_DUNG_2: self.su_dung_2,
        }

    def load(self, item_dic):
        self.ten_he_thong = item_dic.get('Tên hệ thống', 'N/A')
        self.ip = item_dic.get('Địa chỉ IP', 'N/A')
        self.dia_diem = item_dic.get('Địa điểm', 'N/A')
        self.loai = item_dic.get('Loại', 'N/A')
        self.so_card_dk = item_dic.get('Số card ĐK', 'N/A')
        self.cong_ge = item_dic.get('Cổng GE (6)', 'N/A')
        self.cong_10ge = item_dic.get('Cổng 10GE (7)', 'N/A')
        self.lt4 = item_dic.get('LT4 (1)', 'N/A')
        self.lt8 = item_dic.get('LT8 (2)', 'N/A')
        self.lt16 = item_dic.get('LT16 (3)', 'N/A')
        self.su_dung_1 = item_dic.get('Sử dụng (9)', 'N/A')
        self.su_dung_2 = item_dic.get('Sử dụng (11)', 'N/A')

        return self
