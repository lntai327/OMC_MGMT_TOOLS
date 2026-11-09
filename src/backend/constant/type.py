from enum import Enum, auto
from openpyxl.styles import Border, Side, Font, Alignment, PatternFill
from openpyxl.cell.cell import Cell
import colorsys

# Enum for Loại NE
class LoaiNE(Enum):
    CELL2G = auto()
    CELL3G = auto()
    CELL4G = auto()
    CELL5G = auto()
    BTS = auto()
    BSC = auto()
    NODEB = auto()
    ENODEB = auto()
    GNODEB = auto()

class LoaiBTS(Enum):
    BTS_2G = 0
    NODEB_3G = 1
    ENODEB_4G = 2
    GNODEB_5G = 3

class HeThong(Enum):
    _2G = "2G"
    _3G = "3G"
    _4G = "4G"
    _5G = "5G"

# class Symbol(Enum):
#     MORE = "⋮"
#     UP = "🔺"
#     DOWN = "🔻"

########################## EXCEL FORMAT
# style border
EX_FORMAT_THIN_BORDER = Border(
    left=Side(style='thin'),
    right=Side(style='thin'),
    top=Side(style='thin'),
    bottom=Side(style='thin')
)
# Font
EX_FORMAT_TITLE_FONT = Font( # Black color, bold
    bold=True, color="000000", size=14, name="Times New Roman"
)

EX_FORMAT_TITLE_FONT_12 = Font( # Black color, bold
    bold=True, color="000000", size=12, name="Times New Roman"
)

EX_FORMAT_NORMAL_FONT = Font( # Normal
    name="Times New Roman"
)

EX_FORMAT_BOLD_FONT = Font( # BOLD
    bold=True, name="Times New Roman"
)
# Alignment
EX_FORMAT_ALIGNMENT_CENTER = Alignment(horizontal='center', vertical='center')
EX_FORMAT_ALIGNMENT_LEFT = Alignment(horizontal='left', vertical='center')
EX_FORMAT_ALIGNMENT_RIGHT = Alignment(horizontal='right', vertical='center')

# Fill
EX_FORMAT_PATTERN_FILL_HEADER = PatternFill(start_color="00FF7F", end_color="00FF7F", fill_type="solid")

# Format Header cell
def format_header_cell(cell: Cell):
    cell.font = EX_FORMAT_BOLD_FONT
    cell.alignment = EX_FORMAT_ALIGNMENT_CENTER
    cell.fill = EX_FORMAT_PATTERN_FILL_HEADER
    cell.border = EX_FORMAT_THIN_BORDER

# Format Normal cell
def format_normal_cell(cell: Cell):
    cell.border = EX_FORMAT_THIN_BORDER
    try:
        float(cell.value)
        cell.alignment = EX_FORMAT_ALIGNMENT_CENTER
    except:
        pass

#rgba
RGBA_COLORS_L = [
    '#FFC6C6ff', "#d5bbecff", "#93e793ff", '#9edae5ff', "#cece4bff",
    '#dbdb8dff', "#c9dff3ff", "#fba6a5ff", "#a0c499ff", "#dca5ccff",
    "#71c8d2ff", "#c4a8daff", "#aeb4dfff", "#f0ab6fff", 
    '#aec7e8ff', "#f9a4c9ff",
    "#e88888ff", '#c49c94ff',
]

def lighten_color_rgba(rgba_hex_color, amount=0.4):
    rgba_hex_color = rgba_hex_color.lstrip("#")
    r, g, b, a = tuple(int(rgba_hex_color[i:i+2], 16) for i in (0, 2, 4, 6))
    # Normalize to 0–1
    r, g, b = [x/255.0 for x in (r, g, b)]
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    l = min(1, l + amount * (1 - l))  # shift toward white
    r, g, b = colorsys.hls_to_rgb(h, l, s)
    return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}{a:02x}"

PLOT_MARKERS_L = [
            "o", #circle
            "v", #triangle_down
            "^", #triangle_up
            "<", #triangle_left
            ">", #triangle_right
            "s", #square
            "P", #plus (filled)
            "*", #star
            "X", #x (filled)
            "d" #thin_diamond
            ]

PLOT_LINE_STYLES_L = [
            '-', # solid
            '--', # dashed
            ':', # dotted
            '-.', # dashdot
            (0, (1, 1)), # densely dotted
            (5, (10, 3)), # long dash with offset
            (0, (5, 1)), # densely dashed
            (0, (3, 5, 1, 5)), # dashdotted
            (0, (3, 1, 1, 1)), # densely dashdotted
            ]