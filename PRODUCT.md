# EduAlert — sản phẩm hiện tại

Cổng hỗ trợ cố vấn học tập cho bài thi giữa kỳ nhóm 5A. Dùng dữ liệu giả lập, ưu tiên khả năng giải thích, phân biệt xét điều kiện học vụ theo cấu hình và điểm nguy cơ sớm. Không dùng ML, AI trả phí hoặc dịch vụ đám mây.

Stack: Python/FastAPI, Jinja2, CSS/JavaScript thuần, Chart.js cục bộ, SQLAlchemy/Alembic, SQLite, Pydantic, pytest. Có quản trị viên và cố vấn, kiểm tra quyền phía server, Argon2, session/CSRF. Chín giao diện: đăng nhập, tổng quan, danh sách sinh viên, hồ sơ, CSV, cấu hình, can thiệp, báo cáo, quản trị.

Tác vụ chính: tìm sinh viên cần hỗ trợ → hiểu từng yếu tố → thử kịch bản → lưu hồ sơ can thiệp → theo dõi. Quản trị nhập CSV qua xem trước/xác nhận và kích hoạt phiên bản cấu hình có xem trước ảnh hưởng. Các dữ liệu đánh giá đã lưu giữ cấu hình và input riêng.

Phong cách giao diện kế thừa DESIGN.md: nền sáng, sidebar xanh ngọc đậm, chữ Segoe UI, bảng thoáng, màu đỏ/hổ phách/xanh kèm nhãn. Theo yêu cầu mới, biểu đồ dùng Chart.js và có bảng dữ liệu thay thế. Chi tiết triển khai và giới hạn xác minh ở docs/testing.md; hiện chưa chạy được runtime vì phụ thuộc/mạng bị chặn.
