# from openpyxl import load_workbook
# from openpyxl.styles import Font, PatternFill, Alignment, Border
from openpyxl.utils import get_column_letter
from copy import copy

class ExcelHandleUtil:
    def __init__(self):
      pass

    def copy_cell_style(self, source_cell, target_cell):
        """Copy cell style (font, fill, alignment, border) from source to target"""
        if source_cell.has_style:
            target_cell.font = copy(source_cell.font)
            target_cell.fill = copy(source_cell.fill)
            target_cell.alignment = copy(source_cell.alignment)
            target_cell.border = copy(source_cell.border)
            target_cell.number_format = copy(source_cell.number_format)

    def copy_rows_with_formatting(self, ws, from_row, to_row, from_col, to_col, target_row, target_col):
        """
        Copy rows with values, formatting, and merged cells

        Args:
            ws: Worksheet object
            from_row: Starting row (1-indexed)
            to_row: Ending row (1-indexed, inclusive)
            from_col: Starting column (1-indexed)
            to_col: Ending column (1-indexed, inclusive)
            target_row: Target starting row (1-indexed)
            target_col: Target starting column (1-indexed)
        """
        # Calculate dimensions
        num_rows = to_row - from_row + 1
        num_cols = to_col - from_col + 1
        
        # 1. Copy cell values and styles
        for row_offset in range(num_rows):
            for col_offset in range(num_cols):
                source_cell = ws.cell(from_row + row_offset, from_col + col_offset)
                target_cell = ws.cell(target_row + row_offset, target_col + col_offset)
                
                # Copy value
                target_cell.value = source_cell.value
                # Copy style
                self.copy_cell_style(source_cell, target_cell)
        
        # 2. Copy merged cells
        merged_ranges_to_add = []
        for merged_range in ws.merged_cells.ranges:
            # Check if merged range overlaps with source area
            if (from_row <= merged_range.min_row <= to_row or 
                from_row <= merged_range.max_row <= to_row or
                (merged_range.min_row < from_row and merged_range.max_row > to_row)):
                
                # Calculate if merged range is within our copy area
                if (merged_range.min_col <= to_col and merged_range.max_col >= from_col and
                    merged_range.min_row <= to_row and merged_range.max_row >= from_row):
                    
                    # Calculate offset for merged range
                    min_row_offset = max(0, merged_range.min_row - from_row)
                    max_row_offset = min(num_rows - 1, merged_range.max_row - from_row)
                    min_col_offset = max(0, merged_range.min_col - from_col)
                    max_col_offset = min(num_cols - 1, merged_range.max_col - from_col)
                    
                    # Create new merged range at target location
                    new_min_row = target_row + min_row_offset
                    new_max_row = target_row + max_row_offset
                    new_min_col = target_col + min_col_offset
                    new_max_col = target_col + max_col_offset
                    
                    merged_ranges_to_add.append(f"{get_column_letter(new_min_col)}{new_min_row}:{get_column_letter(new_max_col)}{new_max_row}")
        
        # Add merged ranges
        for merged_range in merged_ranges_to_add:
            ws.merge_cells(merged_range)

    def remove_row(self, ws, start_row, end_row):
        rows_to_delete = end_row - start_row + 1
        if rows_to_delete > 0:
            ws.delete_rows(idx=start_row, amount=rows_to_delete)

    def remove_column(self, ws, start_col, end_col):
        cols_to_delete = end_col - start_col + 1
        if cols_to_delete > 0:
            ws.delete_cols(idx=start_col, amount=cols_to_delete)