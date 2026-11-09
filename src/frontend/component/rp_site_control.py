import flet as ft

from share.util.dynamic_info_util import DynamicInfoUtil
from share.constant import constant as SC
from share.constant import type as ST
from share.util.logger_util import LoggerUtil


class RpSiteControl(ft.RadioGroup):
    """Site selection radio group.

    Reads/writes the selected site to DynamicInfoUtil automatically.
    """

    def __init__(self):
        initial = DynamicInfoUtil().get_value(2, SC.K_SCREEN_INPUT, SC.K_SITE1) \
            or ST.Site.ALL_SITE.value

        super().__init__(
            value=initial,
            on_change=self._on_change,
            content=ft.Row(
                controls=[
                    ft.Radio(value=ST.Site.DONG.value, label="Đông"),
                    ft.Radio(value=ST.Site.TAY.value, label="Tây"),
                    ft.Radio(value=ST.Site.ALL_SITE.value, label="Tất Cả Site"),
                ],
                spacing=8,
            ),
        )

    def _on_change(self, e: ft.ControlEvent):
        try:
            DynamicInfoUtil().set_value(e.data, 2, SC.K_SCREEN_INPUT, SC.K_SITE1)
            # LoggerUtil.get_logger().debug(f"RpSiteControl: site changed to {e.data}")
        except Exception as ex:
            LoggerUtil.get_logger().error(f"RpSiteControl._on_change error: {ex}")
