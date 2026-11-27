from typing import Optional
from sqlalchemy import BigInteger, String, Text, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, TimestampMixin

from app.constant import constant as SC


class MegawanMetronetMd(Base, TimestampMixin):
    __tablename__ = "megawan_metronet"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    last_update: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    ma_tb: Mapped[Optional[str]] = mapped_column(String(500), nullable=True, index=True)
    ma_lt_ma_tb_sub: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    ten_th_bao: Mapped[Optional[str]] = mapped_column(String(500), nullable=True, index=True)
    dia_chi: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    diem_cuoi: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    svlan_cvlan: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    ten_thbi: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    ip_thbi: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    port_thbi: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    upe: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    ip_kh: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    ip_gw: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    loai_hinh_tb: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    toc_do: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    loai_kenh: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    trang_thai: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    cap_odf: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    ghi_chu: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


    __table_args__ = (
        Index("idx_megawan_multi_search", "loai_hinh_tb", "ten_th_bao", "loai_kenh"),
    )

    def to_dict(self) -> dict:
        return {
            SC.K_ID: self.id,
            SC.K_LAST_UPDATE: self.last_update,
            SC.K_MA_TB: self.ma_tb,
            SC.K_MA_LT_MA_TB_SUB: self.ma_lt_ma_tb_sub,
            SC.K_TEN_TH_BAO: self.ten_th_bao,
            SC.K_DIA_CHI: self.dia_chi,
            SC.K_DIEM_CUOI: self.diem_cuoi,
            SC.K_SVLAN_CVLAN: self.svlan_cvlan,
            SC.K_TEN_THBI: self.ten_thbi,
            SC.K_IP_THBI: self.ip_thbi,
            SC.K_PORT_THBI: self.port_thbi,
            SC.K_UPE: self.upe,
            SC.K_IP_KH: self.ip_kh,
            SC.K_IP_GW: self.ip_gw,
            SC.K_LOAI_HINH_TB: self.loai_hinh_tb,
            SC.K_TOC_DO: self.toc_do,
            SC.K_LOAI_KENH: self.loai_kenh,
            SC.K_TRANG_THAI: self.trang_thai,
            SC.K_CAP_ODF: self.cap_odf,
            SC.K_GHI_CHU: self.ghi_chu,
        }

