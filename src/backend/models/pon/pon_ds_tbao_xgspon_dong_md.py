from sqlalchemy import Column, Integer, Unicode

from backend.db.database import Base
from share.util.time_util import TimeUtil
from share.constant import constant as SC

class DsTbaoXgsponDongMd(Base):
    """ORM model mapping to table."""

    __tablename__ = "pon_ds_tbao_xgspon_dong"
    __table_args__ = {"implicit_returning": False}

    id = Column(Integer, primary_key=True, autoincrement=True)
    last_update = Column(
        Unicode(100), default=TimeUtil().get_detail_current_time_str
    )
    tram = Column(Unicode(100), nullable=True)
    th_bao = Column(Unicode(200))
    kh_hang = Column(Unicode(200))
    dia_chi = Column(Unicode(500))
    ten_he_thong = Column(Unicode(100), nullable=False)
    slot = Column(Unicode(50), nullable=True)
    port = Column(Unicode(50), nullable=True)
    vpi = Column(Unicode(50), nullable=True)
    cg_nghe = Column(Unicode(50), nullable=False)

    def __repr__(self) -> str:
        return f"<DsTbaoXgsponDongMd(id={self.id}, ten_he_thong={self.ten_he_thong!r})>"

    def to_dict(self) -> dict:
        return {
            SC.K_TRAM: self.tram,
            SC.K_THBAO: self.th_bao,
            SC.K_KH_HANG: self.kh_hang,
            SC.K_DIA_CHI: self.dia_chi,
            SC.K_TEN_HE_THONG: self.ten_he_thong,
            SC.K_SLOT: self.slot,
            SC.K_PORT: self.port,
            SC.K_VPI: self.vpi,
            SC.K_CONG_NGHE: self.cg_nghe,
        }

    def load(self, item_dic) -> 'DsTbaoXgsponDongMd':
        self.tram = item_dic.get('Trạm', 'N/A')
        self.th_bao = item_dic.get('Mã TB', 'N/A')
        self.kh_hang = item_dic.get('Tên TB', 'N/A')
        self.dia_chi = item_dic.get('Địa chỉ lắp đặt', 'N/A')
        self.ten_he_thong = item_dic.get('SYSTEM', 'N/A')
        self.slot = item_dic.get('SLOT', 'N/A')
        self.port = item_dic.get('PORT', 'N/A')
        self.vpi = item_dic.get('VPI', 'N/A')
        self.cg_nghe = item_dic.get('Công nghệ', 'N/A')

        return self
