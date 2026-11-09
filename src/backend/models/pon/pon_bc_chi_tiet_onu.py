from sqlalchemy import Column, Integer, Unicode

from backend.db.database import Base
from share.util.time_util import TimeUtil
from share.constant import constant as SC

class BcChiTietOnuMd(Base):
    """ORM model mapping to table."""

    __tablename__ = "pon_bc_chtiet_onu"
    __table_args__ = {"implicit_returning": False}

    id = Column(Integer, primary_key=True, autoincrement=True)
    last_update = Column(
        Unicode(100), default=TimeUtil().get_detail_current_time_str
    )
    tinh = Column(Unicode(200))
    dvi_qly = Column(Unicode(200))
    tram = Column(Unicode(200))
    ten_he_thong = Column(Unicode(100), nullable=False)
    ip = Column(Unicode(100))
    frame  = Column(Unicode(50))
    slot = Column(Unicode(50))
    port = Column(Unicode(50))
    onu  = Column(Unicode(50))
    serial = Column(Unicode(100))
    loai_onu = Column(Unicode(100))
    ten_onu = Column(Unicode(100))
    th_bao = Column(Unicode(200))
    duplicated = Column(Unicode(200))

    def __repr__(self) -> str:
        return f"<BcChiTietOnuMd(id={self.id}, ten_he_thong={self.ten_he_thong!r})>"

    def to_dict(self) -> dict:
        return {
            SC.K_TINH: self.tinh,
            SC.K_DVI_QLY: self.dvi_qly,
            SC.K_TRAM: self.tram,
            SC.K_TEN_HE_THONG: self.ten_he_thong,
            SC.K_IP: self.ip,
            SC.K_FRAME: self.frame,
            SC.K_SLOT: self.slot,
            SC.K_PORT: self.port,
            SC.K_ONU: self.onu,
            SC.K_SERIAL: self.serial,
            SC.K_LOAI_ONU: self.loai_onu,
            SC.K_TEN_ONU: self.ten_onu,
            SC.K_THBAO: self.th_bao,
            SC.K_DUPLICETED: self.duplicated,
        }

    def load(self, item_dic) -> 'BcChiTietOnuMd':
        self.tinh = item_dic.get('Tỉnh/TP', 'N/A')
        self.dvi_qly = item_dic.get('Đơn vị quản lý', 'N/A')
        self.tram = item_dic.get('Tên nhà trạm', 'N/A')
        self.ten_he_thong = item_dic.get('System name', 'N/A')
        self.ip = item_dic.get('Manager ip', 'N/A')
        self.frame = item_dic.get('Frame no', 'N/A')
        self.slot = item_dic.get('Slot no', 'N/A')
        self.port = item_dic.get('Port no', 'N/A')
        self.onu = item_dic.get('Onu index', 'N/A')
        self.serial = item_dic.get('Serial number', 'N/A')
        self.loai_onu = item_dic.get('Loại Onu', 'N/A')
        self.ten_onu = item_dic.get('Tên Onu', 'N/A')
        self.th_bao = item_dic.get('Tên thuê bao', 'N/A')

        return self
