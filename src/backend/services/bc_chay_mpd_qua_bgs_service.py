from collections import defaultdict
import locale

from backend.constant import type as T
from share.util.logger_util import LoggerUtil
from share.util.dynamic_info_util import DynamicInfoUtil

# Fixed data
from backend.repositories.common_csht_ccl_repo import CshtCclService
from backend.repositories.bc_bts.excel_nodeb3g.excel_nodeb3g_maker import ExcelNodeb3gSheetMaker
from backend.repositories.bc_bts.excel_enodeb4g.excel_enodeb4g_maker import ExcelEnodeb4gSheetMaker
from backend.repositories.bc_bts.excel_gnodeb5g.excel_gnodeb5g_maker import ExcelGnodeb5gSheetMaker
from backend.repositories.common.excel_tht_ttvt.excel_tht_ttvt_maker import ExcelThtTtvtMaker
# Input
from backend.repositories.bc_bts.excel_rp_alarm_chay_mpd.excel_rp_alarm_maker import ExcelRpAlarmMaker
# Output
from backend.repositories.bc_bts.excel_bc_chay_mpd_qua_bgs.excel_bc_chay_mpd_qua_bgs_writer \
    import ExcelBcMpdWriter, DataBcTgHop

from share.constant import constant as SC
from share.constant import type as ST
from share.util.convert import safe_sort_date_time, safe_sort_value, to_int

class BcChayMpdQuaBgsService:
    def __init__(self, ui_set_error_callback=None):
        locale.setlocale(locale.LC_ALL, 'vi_VN.UTF-8')

        self._init_data()

        self._ui_set_error_callback = ui_set_error_callback

        self._csht_ccl_service = CshtCclService()
        self._nodeb3g_sheet_maker = ExcelNodeb3gSheetMaker()
        self._enodeb4g_sheet_maker = ExcelEnodeb4gSheetMaker()
        self._gnodeb5g_sheet_maker = ExcelGnodeb5gSheetMaker()
        self._rp_alarm_maker = ExcelRpAlarmMaker(ui_set_error_callback)
        self._tht_ttvt_maker = ExcelThtTtvtMaker()

    def _init_data(self):
        self._data_bc_chi_tiet_list = []
        self._data_bc_chi_tiet_nclr_list = []
        self._data_bc_tghop = DataBcTgHop([], [])

    def _prepare_data(self):
        self._csht_ccl_service.load()
        self._nodeb3g_sheet_maker.load()
        self._enodeb4g_sheet_maker.load()
        self._gnodeb5g_sheet_maker.load()
        self._rp_alarm_maker.load()
        self._tht_ttvt_maker.load()

        self._bts_all_items_ten_tren_hthong_dict = {}
        for item in self._gnodeb5g_sheet_maker.gnodeb5g_items_list_all:
            self._bts_all_items_ten_tren_hthong_dict[
                (item[SC.K_TEN_TREN_HE_THONG_COMPACT])
            ] = item

        for item in self._enodeb4g_sheet_maker.enodeb4g_items_list_all:
            self._bts_all_items_ten_tren_hthong_dict[
                (item[SC.K_TEN_TREN_HE_THONG_COMPACT])
            ] = item

        for item in self._nodeb3g_sheet_maker.nodeb3g_items_list_all:
            self._bts_all_items_ten_tren_hthong_dict[
                (item[SC.K_TEN_TREN_HE_THONG_COMPACT])
            ] = item

    def _make_data_bc_chi_tiet_item(self, item_dict):
        _item = {}
        _item[SC.K_STT] = 0
        _item[SC.K_NE] = item_dict[SC.K_TEN_NE]
        _item[SC.K_UI_TG_SU_CO2] = item_dict[SC.K_TG_SU_CO_1]
        _item[SC.K_UI_TG_CLR1] = item_dict[SC.K_TG_CLR]
        _item[SC.K_UI_TG_CBAO1] = to_int(item_dict[SC.K_TG_CBAO], force=False)
        _item[SC.K_UI_VNP_GHI_CHU1] = item_dict[SC.K_VNP_GHI_CHU]
        _item[SC.K_UI_TINH_GHI_CHU1] = item_dict[SC.K_TINH_GHI_CHU]
        _item[SC.K_UI_LOAI_SU_CO1] = item_dict[SC.K_LOAI_SU_CO]
        _item[SC.K_UI_TG_CBAO_AC] = item_dict[SC.K_TIME_AC]
        _item[SC.K_UI_PHAN_LOAI_TRAM] = item_dict[SC.K_PHAN_LOAI_TRAM]

        try:
            ma_csht = self._bts_all_items_ten_tren_hthong_dict\
                [(item_dict[SC.K_TEN_TREN_HE_THONG_COMPACT])]\
                [SC.K_MA_CSHT]
            _item[SC.K_UI_TEN_TRAM] = self._bts_all_items_ten_tren_hthong_dict\
                [(item_dict[SC.K_TEN_TREN_HE_THONG_COMPACT])]\
                [SC.K_TEN_QUAN_LY]
        except KeyError as e:
            msg = f'{SC.K_UI_MSG_KTTHAY_NE}'
            LoggerUtil.get_logger().warning(
                f'BcChayMpdQuaBgsService _make_data_bc_chi_tiet_item {_item[SC.K_NE]} {msg} {e}'
            )
            if self._ui_set_error_callback: self._ui_set_error_callback(_item[SC.K_NE], msg)
            ma_csht = SC.K_UI_MSG_MISS_DB
            _item[SC.K_UI_TEN_TRAM] = SC.K_UI_MSG_MISS_DB
            _item[SC.K_UI_DON_VI_QUAN_LY] = SC.K_UI_MSG_MISS_DB
            _item[SC.K_TTVT_2] = SC.K_UI_MSG_MISS_DB

            return _item

        if ma_csht == "":
            msg = f'{SC.K_UI_MSG_KGAN_CSHT}'
            if self._ui_set_error_callback: self._ui_set_error_callback(_item[SC.K_NE], msg)
            LoggerUtil.get_logger().warning(
                (f'BcChayMpdQuaBgsService _make_data_bc_chi_tiet_item failed {_item[SC.K_NE]} : {msg}'))
            _item[SC.K_UI_DON_VI_QUAN_LY] = SC.K_UI_MSG_MISS_DB
            _item[SC.K_TTVT_2] = SC.K_UI_MSG_MISS_DB
            return _item

        try:
            _item[SC.K_UI_DON_VI_QUAN_LY] = \
                self._csht_ccl_service.csht_mdsd_items_ma_csht_dict[ma_csht][SC.K_TEN_DVI_QLY]
            _item[SC.K_TTVT_2] = \
                self._csht_ccl_service.csht_mdsd_items_ma_csht_dict[ma_csht][SC.K_TEN_TTVT_TRAM_VT_NETX]
        except KeyError as e:
            LoggerUtil.get_logger().warning(
                (f'BcChayMpdQuaBgsService _make_data_bc_chi_tiet_item MACSHT key {e}'))
            msg = f'{SC.K_UI_MSG_KGAN_CSHT}'
            if self._ui_set_error_callback: self._ui_set_error_callback(_item[SC.K_NE], msg)
            _item[SC.K_UI_DON_VI_QUAN_LY] = SC.K_UI_MSG_MISS_DB
            _item[SC.K_TTVT_2] = SC.K_UI_MSG_MISS_DB

        return _item

    def _sort_data_bc_chi_tiet(self, data_bc_chi_tiet_item_list):
        data_bc_chi_tiet_item_list_sorted = []

        # sort Đơn vị quản lý: to ha tang -> TTVT -> NE -> Thời gian sự cố
        data_bc_chi_tiet_item_list.sort(
            key=lambda x: (
                safe_sort_value(locale.strxfrm(x[SC.K_UI_DON_VI_QUAN_LY])),
                safe_sort_value(locale.strxfrm(x[SC.K_TTVT_2])),
                safe_sort_value(locale.strxfrm(x[SC.K_NE])),
                safe_sort_date_time(x[SC.K_UI_TG_SU_CO2], "%d/%m/%Y %H:%M:%S"),
            )
        )

        data_bc_chi_tiet_item_list_dvi_qly_dict = defaultdict(list)
        for item in data_bc_chi_tiet_item_list:
            data_bc_chi_tiet_item_list_dvi_qly_dict[item[SC.K_UI_DON_VI_QUAN_LY]].append(item)

        #sort site
        data_bc_chi_tiet_item_list_dvi_qly_dict_bdh = {}
        data_bc_chi_tiet_item_list_dvi_qly_dict_gli = {}
        data_bc_chi_tiet_item_list_dvi_qly_dict_x = {}

        for to_ha_tang, data_bc_chi_tiet_item_list_thtang_x in \
                data_bc_chi_tiet_item_list_dvi_qly_dict.items():
            try:
                site: str = self._tht_ttvt_maker.tht_dict[str(to_ha_tang).lower()][SC.K_SITE1]
                match site.lower():
                    case ST.Site.DONG.value:
                        data_bc_chi_tiet_item_list_dvi_qly_dict_bdh[to_ha_tang] = data_bc_chi_tiet_item_list_thtang_x
                    case ST.Site.TAY.value:
                        data_bc_chi_tiet_item_list_dvi_qly_dict_gli[to_ha_tang] = data_bc_chi_tiet_item_list_thtang_x
            except:
                LoggerUtil.get_logger().error(
                    f'BcChayMpdQuaBgsService _sort_data_bc_chi_tiet failed {to_ha_tang}')
                data_bc_chi_tiet_item_list_dvi_qly_dict_x[to_ha_tang] = data_bc_chi_tiet_item_list_thtang_x

        data_bc_chi_tiet_item_list_dvi_qly_dict = data_bc_chi_tiet_item_list_dvi_qly_dict_bdh | \
                                               data_bc_chi_tiet_item_list_dvi_qly_dict_gli | \
                                               data_bc_chi_tiet_item_list_dvi_qly_dict_x

        # output sorted
        for tht, item_list_ne_x in data_bc_chi_tiet_item_list_dvi_qly_dict.items():
            data_bc_chi_tiet_item_list_sorted.extend(item_list_ne_x)

        return data_bc_chi_tiet_item_list_sorted

    def _make_data_bc_chi_tiet(self): #& CBAO NCLR
        for item in self._rp_alarm_maker.rp_alarm_items_list_all:
            ret = self._make_data_bc_chi_tiet_item(item)

            if str(item[SC.K_TTHAI_CLR]).lower() == SC.K_CLR.lower():
                self._data_bc_chi_tiet_list.append(ret)
            else:
                ret[SC.K_UI_GHI_CHU] = "Đề nghị kiểm tra lại"
                self._data_bc_chi_tiet_nclr_list.append(ret)

        try:
            self._data_bc_chi_tiet_list = self._sort_data_bc_chi_tiet(self._data_bc_chi_tiet_list)
        except Exception as e:
            LoggerUtil.get_logger().error(
                f'BcChayMpdQuaBgsService _make_data_bc_chi_tiet sort _data_bc_chi_tiet_list failed due to {e}'
            )

        try:
            self._data_bc_chi_tiet_nclr_list = self._sort_data_bc_chi_tiet(self._data_bc_chi_tiet_nclr_list)
        except Exception as e:
            LoggerUtil.get_logger().error(
                f'BcChayMpdQuaBgsService _make_data_bc_chi_tiet sort _data_bc_chi_tiet_nclr_list failed due to {e}'
            )

    def _sort_data_table_bc_tghop(self, data_table_bc_tghop_list):
        data_table_bc_tghop_list_sorted = []

        # sort Đơn vị quản lý
        data_table_bc_tghop_list_dvi_qly_dict = defaultdict(list)
        for item in data_table_bc_tghop_list:
            data_table_bc_tghop_list_dvi_qly_dict[item[SC.K_UI_DON_VI_QUAN_LY]].append(item)
        data_table_bc_tghop_list_dvi_qly_dict = dict(
            sorted(
                data_table_bc_tghop_list_dvi_qly_dict.items(),
                key=lambda item: locale.strxfrm(item[0])
            )
        )
        for dvi_qly, data_table_bc_tghop_list_dvi_qly_x \
                in data_table_bc_tghop_list_dvi_qly_dict.items():
            # sort TTVT
            data_table_bc_tghop_list_dvi_qly_x.sort(
                key=lambda x: locale.strxfrm(x[SC.K_TTVT_2])
            )

            # output sorted
            data_table_bc_tghop_list_sorted.extend(data_table_bc_tghop_list_dvi_qly_x)

        return data_table_bc_tghop_list_sorted

    def _make_data_bc_tghop_clr_item(self, ttvt_dict):
        item = {}
        item[SC.K_UI_DON_VI_QUAN_LY] = ttvt_dict[SC.K_TO_HA_TANG]
        item[SC.K_TTVT_2] = ttvt_dict[SC.K_TTVT]

        item[SC.K_UI_SO_LAN] = 0
        item[SC.K_UI_THOI_GIAN] = 0
        for v in self._data_bc_chi_tiet_list:
            if str(v[SC.K_TTVT_2]).lower() == str(item[SC.K_TTVT_2]).lower():
                item[SC.K_UI_SO_LAN] += 1
                try:
                    item[SC.K_UI_THOI_GIAN] += float(v[SC.K_UI_TG_CBAO1])
                except ValueError as e:
                    LoggerUtil.get_logger().warning(f'_make_data_bc_tghop_clr_item key {e}')

        return item

    def _make_data_bc_tghop_nclr_item(self, ttvt_dict):
        item = {}
        item[SC.K_UI_DON_VI_QUAN_LY] = ttvt_dict[SC.K_TO_HA_TANG]
        item[SC.K_TTVT_2] = ttvt_dict[SC.K_TTVT]

        item[SC.K_UI_CBAO_NCLR] = 0
        for v in self._data_bc_chi_tiet_nclr_list:
            if str(v[SC.K_TTVT_2]).lower() == str(item[SC.K_TTVT_2]).lower():
                item[SC.K_UI_CBAO_NCLR] += 1

        return item

    def _make_data_bc_tghop(self):
        site: str = DynamicInfoUtil().get_value(2, SC.K_SCREEN_INPUT, SC.K_SITE1)

        for ttvt_dict in self._tht_ttvt_maker.ttvt_list:
            if site.lower() == ST.Site.ALL_SITE.value:
                pass
            elif site.lower() not in str(ttvt_dict[SC.K_SITE1]).lower():
                continue

            self._data_bc_tghop.cbao_clr_item_list.append(
                self._make_data_bc_tghop_clr_item(ttvt_dict)
            )
            self._data_bc_tghop.cbao_nclr_item_list.append(
                self._make_data_bc_tghop_nclr_item(ttvt_dict)
            )

        # sort
        self._data_bc_tghop.cbao_clr_item_list = \
            self._sort_data_table_bc_tghop(self._data_bc_tghop.cbao_clr_item_list)
        self._data_bc_tghop.cbao_nclr_item_list = \
            self._sort_data_table_bc_tghop(self._data_bc_tghop.cbao_nclr_item_list)

        # make row Tổng
        item = {}
        item[SC.K_UI_DON_VI_QUAN_LY] = ""
        item[SC.K_TTVT_2] = "Tổng"
        item[SC.K_UI_SO_LAN] = sum(
            [x[SC.K_UI_SO_LAN] for x in self._data_bc_tghop.cbao_clr_item_list])
        item[SC.K_UI_THOI_GIAN] = sum(
            [x[SC.K_UI_THOI_GIAN] for x in self._data_bc_tghop.cbao_clr_item_list]
        )
        self._data_bc_tghop.cbao_clr_item_list.insert(0, item)

        #
        item = {}
        item[SC.K_UI_DON_VI_QUAN_LY] = ""
        item[SC.K_TTVT_2] = "Tổng"
        item[SC.K_UI_CBAO_NCLR] = sum(
            [x[SC.K_UI_CBAO_NCLR] for x in self._data_bc_tghop.cbao_nclr_item_list]
        )
        self._data_bc_tghop.cbao_nclr_item_list.insert(0, item)

    def make_bc_chay_mpd_qua_bgs(self) -> str|None:
        ret_path = None

        # init data
        self._init_data()
        # prepare data
        self._prepare_data()
        # make BC Chi Tiết & CANHBAO_NCLR
        self._make_data_bc_chi_tiet()
        # make BC Tong hop
        self._make_data_bc_tghop()

        writer = ExcelBcMpdWriter()
        ret_path = writer.write_excel(
            self._data_bc_chi_tiet_list,
            self._data_bc_chi_tiet_nclr_list,
            self._data_bc_tghop,
        )

        return ret_path