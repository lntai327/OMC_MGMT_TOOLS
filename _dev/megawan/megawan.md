# Design patterns:
refer to "QlyHsuatGponPage"

# Feature :
## manage data : select/delete/update(dialog)/create(dialog) data : MegawanMetronetMd
"data field":
    SC.K_KH_HANG,
    SC.K_DIA_CHI,
    SC.K_DIEM_CUOI,
    SC.K_LOAI_CAP,
    SC.K_LOAI_KENH,
    SC.K_IP_SRC,
    SC.K_IP_DES,
    SC.K_DSLAM,
    SC.K_FSP,
    SC.K_SWITCH,
    SC.K_PORT_SWITCH,
    SC.K_SVLAN_CVLAN,
    SC.K_TOC_DO,
    SC.K_CAP_ADSL,
    SC.K_CAP_ODF,
    SC.K_LAST_UPDATE,
    SC.K_LOAI_DUONG_TRUYEN,
    SC.K_GHI_CHU,

## Cập nhật CSDL :
CSDL : SC.K_EXCEL_MEGAWAN
refer QlyHsuatGponPage implementation for design

## Export excel file:
column: STT + "data field": to implement in "megawan_service"
display LoadingOverlay in center screen while exporting (refer "QlyHsuatGponPage")

## Filter/Search:
- have these input to search exact by column:
SC.K_LOAI_DUONG_TRUYEN
SC.K_KH_HANG
SC.K_DIA_CHI
SC.K_LOAI_CAP
SC.K_LOAI_KENH
SC.K_SVLAN_CVLAN
SC.K_SWITCH
ALL : search value in any "data field"
- have a button to search, do not auto search when search input change

## search/filltered table record:
display direct in page (no dialog), a table scrollable in vertical and horizontal
drag-able to resize column width
refer to QlyHsuatGponPage's tong_hop_table_area

## Detail record display
display direct in page (no dialog)
field:
    "data field",
init with empty value
when select once from search result, value are filled