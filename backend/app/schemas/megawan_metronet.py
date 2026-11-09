from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_serializer


class MegawanBase(BaseModel):
    ma_tb: Optional[str] = None
    ma_lt_ma_tb_sub: Optional[str] = None
    ten_th_bao: Optional[str] = None
    dia_chi: Optional[str] = None
    diem_cuoi: Optional[str] = None
    ip_src: Optional[str] = None
    ip_des: Optional[str] = None
    svlan_cvlan: Optional[str] = None
    cap_adsl: Optional[str] = None
    cap_odf: Optional[str] = None
    ghi_chu: Optional[str] = None
    ip: Optional[str] = None
    ten_he_thong: Optional[str] = None
    port_switch: Optional[str] = None
    upe: Optional[str] = None
    loai_hinh_tb: Optional[str] = None
    trang_thai: Optional[str] = None
    toc_do: Optional[str] = None
    don_vi: Optional[str] = None
    loai_kenh: Optional[str] = None


class MegawanCreate(MegawanBase):
    pass


class MegawanUpdate(MegawanBase):
    pass


class MegawanResponse(MegawanBase):
    id: int
    last_update: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

    @field_serializer("created_at", "updated_at")
    def serialize_dt(self, v: Optional[datetime]) -> Optional[str]:
        return v.isoformat() if v else None


class MegawanFilterParams(BaseModel):
    loai_hinh_tb: Optional[str] = None
    ten_th_bao: Optional[str] = None
    dia_chi: Optional[str] = None
    loai_kenh: Optional[str] = None
    svlan_cvlan: Optional[str] = None
    ten_he_thong: Optional[str] = None
    all_search: Optional[str] = Field(default=None, description="Global keyword matching across all search fields")

