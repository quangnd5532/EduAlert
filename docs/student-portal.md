# Cổng thông tin sinh viên — phiên bản 3.1

Cổng sinh viên có các **trang và URL riêng**, dùng chung bộ khung điều hướng. Không dùng các liên kết neo để gộp tất cả chức năng vào dashboard.

| Đường dẫn | Chức năng |
|---|---|
| `/student/overview` | Thông tin học vụ, kết quả tóm tắt, việc cần theo dõi và biểu đồ GPA |
| `/student/results` | Bảng điểm học kỳ, tìm/lọc học phần, xuất CSV đúng bộ lọc, môn còn nợ, lịch sử GPA/tín chỉ |
| `/student/analysis` | Hai kết quả A/B độc lập, cây điều kiện, đóng góp từng yếu tố và dữ liệu cần bổ sung |
| `/student/planning` | Biểu mẫu mô phỏng kỳ tiếp theo, đối chiếu trước/sau, giả định tính GPA tích lũy |
| `/student/appointments` | Các lịch hẹn/hồ sơ hỗ trợ hiện tại, đề nghị tư vấn được ghi DB |
| `/student/profile` | Hồ sơ, lớp/ngành/khóa, cố vấn và điểm xét tuyển kèm phương thức/thang |

Đăng nhập sinh viên qua tài khoản `student` hoặc mã `000005`; mật khẩu giống admin demo lúc nâng cấp dữ liệu. Các sinh viên khác đăng nhập bằng mã của mình hoặc `sv000001`…; chỉ xem chính hồ sơ đã liên kết. Đăng nhập quản trị/cố vấn tiếp tục dùng các màn hình nghiệp vụ quản lý.

## Tổ chức giao diện

Masthead xanh navy, thương hiệu EduAlert và tên cổng chức năng; không giả mạo tên một trường cụ thể. Thanh công cụ trắng, menu trái theo nhóm Học tập/Hỗ trợ & hồ sơ, breadcrumb, tiêu đề trang và bộ lọc học kỳ. Nội dung dùng bảng và thông tin học vụ trực tiếp, không dùng các khối chức năng lặp lại làm dashboard dài. Trên điện thoại, menu chuyển thành danh mục mở/đóng dùng được bằng bàn phím.

Các trang render dữ liệu bằng Jinja2 ngay trên máy chủ. JavaScript phục vụ biểu đồ và gửi biểu mẫu tương tác; tắt JavaScript vẫn xem được dữ liệu, tính mô phỏng và gửi đề nghị tư vấn bằng POST có CSRF. Nội dung đề nghị không đi vào query string. Menu giữ `semester_id` khi đổi trang. Đổi học kỳ bằng GET, có thể đánh dấu hoặc chia sẻ URL trong cùng quyền truy cập. Lịch hẹn là dữ liệu hiện tại, được ghi nhãn không giới hạn theo kỳ đang xem.

Tìm tên/mã học phần và lọc kết quả ở trang bảng điểm cũng áp dụng cho CSV xuất. API luôn xác định sinh viên từ session, không tin mã sinh viên do client tự gửi. Cố vấn và quản trị không dùng URL cổng cá nhân của sinh viên để vượt phạm vi.

## Dữ liệu và tính đúng

Database đã nâng cấp gồm 60 hồ sơ giả lập, 110 học phần trong danh mục, 2.676 kết quả học phần, 60 tài khoản sinh viên. Điểm môn theo thang 4 và tín chỉ được đối soát với tổng kết học kỳ. GPA tích lũy lấy trung bình theo tín chỉ trong dữ liệu demo có giả định không học lại; missing vẫn là missing. Nguồn sinh dữ liệu: `app/demo_data.py`; cập nhật dữ liệu cũ có backup qua `app/refresh_demo.py`.

Không diễn giải điểm ưu tiên hỗ trợ thành xác suất hoặc độ chính xác dự đoán. Quy tắc học vụ mặc định chỉ là minh họa. Lịch sử đánh giá đã lưu không bị ghi đè khi cập nhật dữ liệu/cấu hình; các trang hiện tại tính trực tiếp theo cấu hình đang áp dụng.

## Chạy bản mới

```powershell
cd C:\Users\Quang\Documents\EduAlert
powershell.exe -NoProfile -ExecutionPolicy RemoteSigned -File .\start.ps1 -Demo
```

Địa chỉ hiện tại: **http://127.0.0.1:8001**. F5 của VS Code khởi động task server và mở địa chỉ này. Phiên server cũ tại8000 có thể vẫn đang giữ mã cũ; không dùng nó để đánh giá giao diện3.1. Nếu sửa Python trong khi server đang chạy, cần khởi động lại server để tải router/template mới.

## Kiểm tra

`pytest` kiểm từng URL, form chỉ nằm ở trang tương ứng, HTML đã có dữ liệu trước khi chạy JavaScript, không có ID trùng, học kỳ được giữ qua điều hướng, CSV khớp bộ lọc, quyền sinh viên/cố vấn và các kỳ không hợp lệ. Các test công thức, đối soát điểm từng môn, transaction/rollback và mô phỏng không ghi đè dữ liệu được giữ lại. Kết quả chạy thực tế và giới hạn kiểm tra trình duyệt được ghi trong `docs/testing.md`.
