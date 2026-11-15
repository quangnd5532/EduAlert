# Giao diện học vụ 3.5 — 14/11/2026

EduAlert dùng chung màu sắc, kiểu chữ và thành phần điều khiển giữa đăng nhập, cổng sinh viên và không gian quản lý. Tài liệu này ghi thay đổi giao diện; không xác nhận nguồn dữ liệu là hồ sơ thật hoặc chứng nhận sẵn sàng triển khai production.

## Nội dung và bố cục

- Trang đăng nhập giới thiệu trực tiếp bảng điểm, mục tiêu học kỳ và lịch tư vấn. Bỏ khẩu hiệu lặp lại và lời giới thiệu mang tính quảng bá.
- Tổng quan sinh viên ưu tiên GPA, tín chỉ, việc cần làm và nút đặt mục tiêu. Trạng thái hỗ trợ được diễn đạt bằng hành động như “Nên trao đổi sớm với cố vấn”.
- Trang phân tích trình bày nhận xét và yếu tố cần chú ý trước; điều kiện chi tiết và cách tính điểm nằm trong các phần mở rộng. Quyết định học vụ chính thức vẫn được phân biệt với kết quả đối chiếu.
- Hồ sơ hiển thị thông tin sinh viên và xét tuyển trước, phần khôi phục tài khoản sau. Nhãn “Phương thức xét tuyển” được giữ thống nhất ở hồ sơ và quản trị.
- Trang lịch tư vấn bỏ cột mã hồ sơ khỏi bảng sinh viên. Các đường dẫn đăng ký tư vấn và cập nhật thông tin vẫn hoạt động.
- Không gian cố vấn/quản trị có mô tả đúng từng trang, biểu tượng theo chức năng và menu dạng mở rộng trên màn hình nhỏ.
- Bỏ nhãn dữ liệu trải nghiệm, chân trang giới thiệu demo, tên trường “giả lập”, hướng dẫn cài thư viện trên giao diện và các câu giải thích kỹ thuật không giúp người dùng thao tác.

## Dữ liệu và giới hạn

Không xóa hoặc sửa hồ sơ, tài khoản, mật khẩu, thông tin khôi phục hay snapshot đánh giá trong database. `presentation.display_text` chỉ chuyển một danh sách nhãn cũ cố định sang cách trình bày phù hợp, như tên bộ đánh giá, hai tên học phần cũ và câu ghi chú mẫu. Nội dung do người sử dụng đặt tên được giữ nguyên. Tài liệu tạo dữ liệu, tài khoản kiểm thử và cấu hình gửi email/SMS vẫn được giữ trong tài liệu vận hành.

Các nội dung ảnh hưởng đến quyết định vẫn được diễn đạt đúng: GPA mục tiêu là ước tính; nguồn và thời gian của kết quả đánh giá vẫn xem được; việc áp dụng quy chế cần do đơn vị đào tạo xác nhận. Không đổi dữ liệu mẫu thành tuyên bố dữ liệu chính thức.

## Trạng thái sử dụng

Thông báo lỗi trường dùng nhãn quen thuộc thay cho đường dẫn kỹ thuật như `body.gpa`. Lỗi mạng hướng dẫn kiểm tra kết nối và thử lại. Danh sách tải lỗi thay thông báo đang tải bằng cách phục hồi rõ ràng. Biểu mẫu có trạng thái đang xử lý, chặn gửi lặp trong lúc chờ và khôi phục nút khi thất bại. Trạng thái lưu kết quả và thời gian cập nhật được gom vào phần chi tiết. Ngày hẹn chỉ có ngày được hiển thị ngày/tháng/năm, không tự đổi ngày theo múi giờ.

## Kiểm tra thực tế

- Toàn bộ 110 kiểm thử Python và 13 kiểm thử JavaScript đạt; còn một cảnh báo deprecation của Starlette/AnyIO.
- Kiểm tra vai trò sinh viên/cố vấn/quản trị, các trang chính, bảo toàn dữ liệu gốc khi đổi nhãn, ẩn thông tin kỹ thuật khỏi phần nội dung chính, thông báo mạng và phục hồi biểu mẫu.
- Server được khởi động lại ở `http://127.0.0.1:8001`; health trả `ok`, phiên bản 3.5.0. Trang đăng nhập, khôi phục mật khẩu và tài nguyên giao diện mới trả HTTP 200.
- Chưa nghiệm thu bố cục bằng ảnh chụp desktop/mobile: công cụ điều khiển trình duyệt báo `The browser access host is unavailable`. Đã rà soát các breakpoint trong CSS; kiểm thử HTML/JavaScript không thay thế quan sát trực quan.
