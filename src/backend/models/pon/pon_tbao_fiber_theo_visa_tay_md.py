from sqlalchemy import Column, Integer, Unicode

from backend.db.database import Base
from share.util.time_util import TimeUtil
from share.constant import constant as SC

class TbaoFiberVisaTayMd(Base):
    """ORM model mapping to table."""

    __tablename__ = "pon_tbao_fiber_visa_tay"
    __table_args__ = {"implicit_returning": False}

    id = Column(Integer, primary_key=True, autoincrement=True)
    last_update = Column(
        Unicode(200), default=TimeUtil().get_detail_current_time_str
    )
    t_khoan = Column(Unicode(500))
    kh_hang = Column(Unicode(500))
    dia_chi = Column(Unicode(500))
    ngay_nghiem_thu = Column(Unicode(200))
    trang_thai = Column(Unicode(200))
    ip = Column(Unicode(100))
    tham_so = Column(Unicode(1500))
    dvu = Column(Unicode(200))
    duplicated = Column(Unicode(200))

    def __repr__(self) -> str:
        return f"<TbaoFiberVisaTayMd(id={self.id}, t_khoan={self.t_khoan!r})>"

    def to_dict(self) -> dict:
        return {
            SC.K_T_KHOAN: self.t_khoan,
            SC.K_KH_HANG: self.kh_hang,
            SC.K_DIA_CHI: self.dia_chi,
            SC.K_NGAY_NGHIEM_THU: self.ngay_nghiem_thu,
            SC.K_TRANG_THAI: self.trang_thai,
            SC.K_IP: self.ip,
            SC.K_THAM_SO: self.tham_so,
            SC.K_DVU: self.dvu,
            SC.K_DUPLICETED: self.duplicated,
        }

    def load(self, item_dic) -> 'TbaoFiberVisaTayMd':
        self.t_khoan = item_dic.get('Tài khoản dịch vụ', 'N/A')
        self.kh_hang = item_dic.get('Tên khách hàng', 'N/A')
        self.dia_chi = item_dic.get('Địa chỉ khách hàng', 'N/A')
        self.ngay_nghiem_thu = item_dic.get('Ngày nghiệm thu', 'N/A')
        self.trang_thai = item_dic.get('Tình trạng sử dụng', 'N/A')
        self.ip = item_dic.get('BrasIP', 'N/A')
        self.tham_so = item_dic.get('Tham số cổng', 'N/A')
        self.dvu = item_dic.get('Gói dịch vụ', 'N/A')

        return self
