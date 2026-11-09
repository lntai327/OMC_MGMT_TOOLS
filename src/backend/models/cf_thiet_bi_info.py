from sqlalchemy import Column, Integer, Unicode

from backend.db.database import Base
from share.constant import constant as SC

class ThBiInfo(Base):
    """ORM model mapping to table."""

    __tablename__ = "cf_thbi_info"
    __table_args__ = {"implicit_returning": False}

    id = Column(Integer, primary_key=True, autoincrement=True)
    phan_loai = Column(Unicode(100))
    ten_card = Column(Unicode(100))
    loai_card = Column(Unicode(100))
    sfp_model_pn = Column(Unicode(100))
    loai_sfp = Column(Unicode(100))
    dong_card = Column(Unicode(100))
    loai_port = Column(Unicode(50))
    loai = Column(Unicode(100))

    def __repr__(self) -> str:
        return f"<ThBiInfo(id={self.id})>"

    def to_dict(self) -> dict:
        return {
            SC.K_PHAN_LOAI: self.phan_loai,
            SC.K_TEN_CARD: self.ten_card,
            SC.K_LOAI_CARD: self.loai_card,
            SC.K_SFP_MODEL_PN: self.sfp_model_pn,
            SC.K_LOAI_SFP: self.loai_sfp,
            SC.K_DONG_CARD: self.dong_card,
            SC.K_LOAI_PORT: self.loai_port,
            SC.K_LOAI: self.loai,
        }
