# MegawanMetronetPage:
## tại {/* 5. MODAL IMPORT FILE EXCEL */}
### hãy thêm chức năng nhập dữ liệu Excel cho file "Thiết bị OLT" vào Model "ThbiAccessMd"
### logic cập nhật dữ liệu:
- không dựa vào Action (DELETE/INSERT)
- Dựa vào so sánh dữ liệu trong Excel và db hiện tại:
ThbiAccessMd.ten_he_thong (SC.K_TEN_HE_THONG) lấy làm key
Nếu key có trong file excel, và đồng thời có trong db -> cập nhật vào db
Nếu key có trong file excel, và không có trong db -> thêm mới vào db
Nếu keu không có trong file excel, nhưng có trong db -> xóa khỏi db

## tại {/* 4. MODAL THÊM / CHỈNH SỬA BẢN GHI */},
### tại "Tên thiết bị"
hãy hiển thị list đề xuất tên thiết bị là DICTINCT của ThbiAccessMd.ten_he_thong, loại trừ record có ThbiAccessMd.chuc_nang khác "GPON"