from sqlalchemy import Column, Integer, Unicode #UnicodeText

from backend.db.database import Base
from share.util.time_util import TimeUtil
from share.constant import constant as SC

class CshtCclMd(Base):
    """ORM model mapping to table."""

    __tablename__ = "common_csht_ccl"
    __table_args__ = {"implicit_returning": False}

    id = Column(Integer, primary_key=True, autoincrement=True)

    ma_csht = Column(Unicode(100))
    ten_csht = Column(Unicode(100))
    ten_dvi_qly = Column(Unicode(100))
    ten_ttvt_tram_vthong_netx = Column(Unicode(100))
    loai_nha_tram = Column(Unicode(100))
    last_update = Column(Unicode(100), default=TimeUtil().get_detail_current_time_str)
    tr_thai_dat_may_no = Column(Unicode(100))
    phuong_xa = Column(Unicode(100))
    dia_chi = Column(Unicode(100))
    ma_loai_csht_ddong = Column(Unicode(100))
    trang_thai = Column(Unicode(100))

    def __repr__(self) -> str:
        return f"<CshtCclMd(id={self.id}, ma_csht={self.ma_csht!r})>"

    def to_dict(self) -> dict:
        return {
            SC.K_MA_CSHT: self.ma_csht,
            SC.K_TEN_CSHT: self.ten_csht,
            SC.K_TEN_DVI_QLY: self.ten_dvi_qly,
            SC.K_TEN_TTVT_TRAM_VT_NETX: self.ten_ttvt_tram_vthong_netx,
            SC.K_LOAI_NHA_TRAM: self.loai_nha_tram,
            SC.K_TRTHAI_DAT_MNO: self.tr_thai_dat_may_no,
            SC.K_PHUONG_XA: self.phuong_xa,
            SC.K_DIA_CHI: self.dia_chi,
            SC.K_MA_LOAI_CSHT_DDONG: self.ma_loai_csht_ddong,
            SC.K_TRANG_THAI: self.trang_thai,
        }

    def load(self, item_dic) -> 'CshtCclMd':
        self.ma_csht = item_dic.get(SC.K_UI_MA_CSHT)
        self.ten_csht = item_dic.get(SC.K_UI_TEN_CSHT)
        self.ten_dvi_qly = item_dic.get(SC.K_UI_TEN_DVI_QLY)
        self.ten_ttvt_tram_vthong_netx = item_dic.get(SC.K_UI_TEN_TTVT_TRAM_VT_NETX)
        self.loai_nha_tram = item_dic.get(SC.K_UI_LOAI_NHA_TRAM)
        self.tr_thai_dat_may_no = item_dic.get(SC.K_UI_TRTHAI_DAT_MNO)
        self.phuong_xa = item_dic.get(SC.K_UI_PHUONG_XA)
        self.dia_chi = item_dic.get(SC.K_UI_DIA_CHI)
        self.ma_loai_csht_ddong = item_dic.get(SC.K_UI_MA_LOAI_CSHT_DI_DONG)
        self.trang_thai = item_dic.get(SC.K_UI_TRANG_THAI)

        return self
