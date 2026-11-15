# EduAlert interface

## Thiết kế hiện hành 3.5 — cổng học vụ

Operate mode cho sinh viên, cố vấn và quản trị. Chung một hệ giao diện tại `static/campus-ui.css`, nạp sau CSS chức năng của từng khu vực. Màu chủ đạo navy `#153958`, liên kết và nút chính `#215f9a`, chữ `#27364b`, chữ phụ `#52677d`, nền `#f2f4f7`, viền `#dbe2e9`, focus vàng đất `#b67a10`. Font Segoe UI/Arial hỗ trợ tiếng Việt, nội dung 13–15px, tiêu đề trang 26px, tiêu đề mục 16–18px. Số liệu dùng tabular; các bảng và nhãn trạng thái luôn có chữ.

Khoảng cách theo nhóm 8/12/16/20/24/32px. Panel bo 10px, ô nhập và nút bo 6px; dùng viền mảnh, không bóng trang trí. Nhãn có chữ, nút diễn đạt hành động cụ thể. Dùng chung biểu tượng SVG nét mảnh và dấu nhận diện mũ tốt nghiệp; màu cảnh báo chỉ dành cho trạng thái cần chú ý.

Thanh đầu trang navy, menu bên trắng rộng 248px, nền nội dung xám nhạt. Không gian quản lý chuyển sang menu native details dưới 820px; cổng sinh viên giữ menu native details dưới 900px. Bảng tự cuộn ngang; dưới 640px biểu mẫu thành một cột và ô nhập đủ lớn cho điện thoại. Chế độ giảm chuyển động tắt hiệu ứng chuyển cảnh.

Trang đăng nhập giới thiệu trực tiếp các chức năng. Tổng quan sinh viên đưa kết quả và việc cần làm lên trước. Phân tích hiển thị nhận xét trước, cách tính điểm trong details. Hồ sơ ưu tiên thông tin sinh viên trước thông tin khôi phục. Nội dung demo, khẩu hiệu và hướng dẫn kỹ thuật không xuất hiện như phần nội dung chính; nguồn dữ liệu mẫu và cấu hình vận hành nằm trong tài liệu. GPA dự kiến và kết quả đối chiếu vẫn được mô tả đúng giới hạn.

Trạng thái đang xử lý, lỗi mạng, không có kết quả, lỗi trường và lưu thành công có nội dung phục hồi cụ thể. Biểu mẫu khóa nút trong lúc gửi và mở lại khi thất bại. Chi tiết nguồn đánh giá được mở theo yêu cầu; không bỏ thông tin cần đối chiếu. Xem `docs/interface-polish.md` về phạm vi kiểm tra và giới hạn kiểm tra trực quan.

## Tham chiếu cổng sinh viên 3.1

Operate mode. Cấu trúc cổng học vụ với masthead navy `#153958`, thanh công cụ và menu nền trắng, nền nội dung `#f2f4f7`, chữ chính `#27364b`, liên kết `#215f9a`, đường phân cách `#dbe2e9`. Dùng Segoe UI/Arial cho dữ liệu và văn bản tiếng Việt. Tiêu đề trang25px, tiêu đề bảng15px, nội dung12–14px; số liệu tabular. Bảng có header nền xám xanh, cột điểm/tín chỉ căn phải, badge có chữ thể hiện trạng thái.

Khung tối đa1440px, sidebar248px; ở900px chuyển menu thành danh mục native details, ở640px các cột thành một cột. Các chức năng là các URL riêng; tổng quan chỉ hiển thị tóm tắt. Biểu mẫu có nhãn, focus3px vàng đất, thông báo lỗi và trạng thái đang gửi. Biểu đồ Chart.js có bảng dữ liệu đi kèm. Print bỏ điều hướng/form, giữ thông tin và bảng. Không có tên nhóm, ảnh người giả hoặc danh tính trường được bịa ra. Xem `app/templates/student/`, `static/student.css` và `static/login.css`.

## Tham chiếu giao diện quản lý ban đầu

Operate mode: bàn làm việc cho cố vấn trên laptop, dùng trong môi trường sáng. Giao diện tiếng Việt, nền xám xanh nhạt, sidebar xanh mực, màu chủ đạo teal; đỏ và hổ phách chỉ dùng cho nguy cơ. Typography Segoe UI hỗ trợ dấu tiếng Việt, số liệu tabular. Khoảng cách 4/8/12/16/24/32px, border radius 12px; panel viền mảnh, không bóng trang trí. Tiêu đề lớn rõ, bảng có hàng thoáng, nội dung ưu tiên hành động hỗ trợ. Biểu đồ SVG có nhãn và dữ liệu bảng đi kèm. Màn hình nhỏ chuyển sidebar thành navigation ngang, bảng cuộn riêng; form có nhãn thật, focus rõ. Dữ liệu mẫu được gắn nhãn xuyên suốt.
