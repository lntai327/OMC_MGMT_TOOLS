from sqlalchemy import Column, Integer, Unicode

from backend.db.database import Base
from share.util.time_util import TimeUtil
from share.constant import constant as SC

class MegawanMetronetMd(Base):
    __tablename__ = "megawan_metronet"
    __table_args__ = {"implicit_returning": False}

    id = Column(Integer, primary_key=True, autoincrement=True)
    last_update = Column(
        Unicode(100), default=TimeUtil().get_detail_current_time_str
    )
    ma_tb = Column(Unicode(500))
    ma_lt_ma_tb_sub = Column(Unicode(500))
    ten_th_bao = Column(Unicode(500))
    dia_chi = Column(Unicode(500))
    diem_cuoi = Column(Unicode(500))
    ip_src = Column(Unicode(500))
    ip_des = Column(Unicode(500))
    svlan_cvlan = Column(Unicode(500))
    cap_adsl = Column(Unicode(500))
    cap_odf = Column(Unicode(500))
    ghi_chu = Column(Unicode(2000))
    ip = Column(Unicode(2000))
    ten_he_thong = Column(Unicode(2000))
    port_switch = Column(Unicode(500))
    upe = Column(Unicode(500))
    loai_hinh_tb = Column(Unicode(500))
    trang_thai = Column(Unicode(500))
    toc_do = Column(Unicode(500))
    don_vi = Column(Unicode(500))
    loai_kenh = Column(Unicode(500))

    def to_dict(self) -> dict:
        return {
            SC.K_ID: self.id,
            SC.K_LAST_UPDATE: self.last_update,
            SC.K_MA_TB: self.ma_tb,
            SC.K_MA_LT_MA_TB_SUB: self.ma_lt_ma_tb_sub,
            SC.K_TEN_TH_BAO: self.ten_th_bao,
            SC.K_DIA_CHI: self.dia_chi,
            SC.K_DIEM_CUOI: self.diem_cuoi,
            SC.K_IP_SRC: self.ip_src,
            SC.K_IP_DES: self.ip_des,
            SC.K_SVLAN_CVLAN: self.svlan_cvlan,
            SC.K_CAP_ADSL: self.cap_adsl,
            SC.K_CAP_ODF: self.cap_odf,
            SC.K_GHI_CHU: self.ghi_chu,
            SC.K_IP: self.ip,
            SC.K_TEN_HE_THONG: self.ten_he_thong,
            SC.K_PORT_SWITCH: self.port_switch,
            SC.K_UPE: self.upe,
            SC.K_LOAI_HINH_TB: self.loai_hinh_tb,
            SC.K_TRANG_THAI: self.trang_thai,
            SC.K_TOC_DO: self.toc_do,
            SC.K_DVI: self.don_vi,
            SC.K_LOAI_KENH: self.loai_kenh,
        }

    def load(self, item_dic) -> 'MegawanMetronetMd':
        self.last_update = item_dic.get('ngaytacdong', 'N/A')
        self.ma_tb = item_dic.get('MÃ TB', 'N/A')
        self.ma_lt_ma_tb_sub = item_dic.get('MÃ LT/MÃ TB SUB', 'N/A')
        self.ten_th_bao = item_dic.get('Tên thuê bao', 'N/A')
        self.dia_chi = item_dic.get('Địa chỉ lắp đặt', 'N/A')
        self.diem_cuoi = item_dic.get('diemcuoi', 'N/A')
        self.ip_src = item_dic.get('ipsource', 'N/A')
        self.ip_des = item_dic.get('ipdes', 'N/A')
        self.svlan_cvlan = item_dic.get('svlancvlan', 'N/A')
        self.cap_adsl = item_dic.get('capadsl', 'N/A')
        self.cap_odf = item_dic.get('capodf', 'N/A')
        self.ghi_chu = item_dic.get('ghichu', 'N/A')
        self.ip = item_dic.get('IP', 'N/A')
        self.ten_he_thong = item_dic.get('system', 'N/A')
        self.port_switch = item_dic.get('portswitch', 'N/A')
        self.upe = item_dic.get('UPE', 'N/A')
        self.loai_hinh_tb = item_dic.get('LOẠI HÌNH TB', 'N/A')
        self.trang_thai = item_dic.get('Trạng thái', 'N/A')
        self.toc_do = item_dic.get('Tốc độ', 'N/A')
        self.don_vi = item_dic.get('Đơn vị', 'N/A')
        self.loai_kenh = item_dic.get('LOẠI KÊNH', 'N/A')

        return self
