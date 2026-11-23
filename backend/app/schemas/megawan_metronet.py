from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_serializer
from app.core.timezone import isoformat_vietnam


class MegawanBase(BaseModel):
    last_update: Optional[str] = None
    ma_tb: Optional[str] = None
    ma_lt_ma_tb_sub: Optional[str] = None
    ten_th_bao: Optional[str] = None
    dia_chi: Optional[str] = None
    diem_cuoi: Optional[str] = None
    svlan_cvlan: Optional[str] = None
    ten_thbi: Optional[str] = None
    ip_thbi: Optional[str] = None
    port_thbi: Optional[str] = None
    upe: Optional[str] = None
    ip_kh: Optional[str] = None
    ip_gw: Optional[str] = None
    loai_hinh_tb: Optional[str] = None
    toc_do: Optional[str] = None
    loai_kenh: Optional[str] = None
    trang_thai: Optional[str] = None
    cap_odf: Optional[str] = None
    ghi_chu: Optional[str] = None

class MegawanCreate(MegawanBase):
    pass


class MegawanUpdate(MegawanBase):
    expected_last_update: Optional[str] = None
    expected_updated_at: Optional[datetime] = None



class MegawanResponse(MegawanBase):
    id: int
    last_update: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

    @field_serializer("created_at", "updated_at")
    def serialize_dt(self, v: Optional[datetime]) -> Optional[str]:
        return isoformat_vietnam(v) if v else None


class MegawanFilterParams(BaseModel):
    loai_hinh_tb: Optional[str] = None
    ten_th_bao: Optional[str] = None
    dia_chi: Optional[str] = None
    loai_kenh: Optional[str] = None
    svlan_cvlan: Optional[str] = None
    ten_thbi: Optional[str] = None
    all_search: Optional[str] = Field(default=None, description="Global keyword matching across all search fields")

