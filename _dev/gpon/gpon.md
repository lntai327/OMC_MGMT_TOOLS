###
Tên card | Loại card
FGLT-B GPON
GVHH COMBO (xgspon)
V922GPHD GPON (replace V922MPCC)
NGLT-C GPON
FGLT-D GPON
FGLT-A GPON
H903GPSF GPON
H905FLHF COMBO (xgspon)
FWLT-C COMBO (xgspon)
H902GPSF GPON
GTGH GPON
GVGO GPON
GFGL GPON
HFTL COMBO (xgspon)
GTGO GPON

###
Model P/N | Loại SFP
Z04042000-Q420 MPM (sfp_combo)
Z04042000-Q318 MPM (sfp_combo)
OM5270S-D2SW MPM (sfp_combo)
OM5270S-N2S N2 (sfp_combo)
3FE47581BB MPM (sfp_combo)
3FE47581BD MPM (sfp_combo)
Còn lại GPON

###
OLT MA5801-GP8	0-15
	MA5800X15	0-15
	MA5800X7	0-15
các OLT còn lại 1-16

###
0/2
Frame/slot

pon:1/1/1/12
rack / shelf / slot / port

GPON 0/1/4 -> shelf / slot / port

###
card: olt và slot là key
sfp: olt slot port là key
onu chi tiết: olt, Tên Onu

###
<!-- Số card PON lắp đặt
	= LT4 (1) + LT8 (2) + LT16 (3) | tong hop thiet bi gpon tren mang.xlsx
	
Cổng PON lắp đặt
 = (LT4 (1) * 4 + LT8 (2) * 8 + LT16 (3) * 6) | tong hop thiet bi gpon tren mang.xlsx

Số ONT sử dụng 
	= Sử dụng (11) | tong hop thiet bi gpon tren mang.xlsx

Cổng PON đang sử dụng
	= Sử dụng (9) | tong hop thiet bi gpon tren mang.xlsx -->

### "Đề xuất port"
# Tô màu cell : hết port
# Thứ tự ưu tiên
1 OLT
1.1 cùng OLT -> có sfp
1.2 cùng OLT -> k có sfp
1.3 khác OLT, cùng CSHT -> có sfp
1.4 khác OLT, cùng CSHT -> k có sfp

2 card (gpon/combo)
2.1 cùng loại card
2.2 khác loại card

3 sfp
gpon - gpon
	 - xgspon combo (mpm)
xgspon combo (mpm) - xgspon combo (mpm)
n2 - n2