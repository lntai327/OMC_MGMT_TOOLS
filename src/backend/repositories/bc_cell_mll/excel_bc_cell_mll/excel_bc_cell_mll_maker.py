from share.constant import constant as SC
from backend.repositories.bc_cell_mll.excel_bc_cell_mll.excel_bc_cell_mll_loader import ExcellBcCellMllLoader

class ExcelBcCellMllMaker():
    def __init__(self):
        self.bc_tghop_ttvt_dict = {}

    def load(self):
        self._loadFromExcel()

    def _loadFromExcel(self):
        bc_tghop_items_list: list = ExcellBcCellMllLoader().load_items()

        for item in bc_tghop_items_list:
            self.bc_tghop_ttvt_dict[item[SC.K_TTVT]] = item.to_dict()