# Khôi phục mật khẩu sinh viên

Trang đăng nhập không hiển thị tài khoản trải nghiệm, dữ liệu mẫu hoặc hướng dẫn cho lập trình viên. Phần giới thiệu tập trung vào kết quả, kế hoạch và kết nối cố vấn. Biểu mẫu được ưu tiên trước trên màn hình nhỏ.

## Luồng sử dụng

1. Sinh viên đăng nhập, vào **Thông tin sinh viên → Thông tin khôi phục tài khoản**. Đăng ký email, số điện thoại hoặc cả hai, xác nhận bằng mật khẩu hiện tại. Thông tin liên hệ được chuẩn hóa, không được trùng tài khoản khác. Hồ sơ cũ không bị gán email/số điện thoại bịa đặt.
2. Tại `/login`, chọn **Quên mật khẩu?**, chọn email hoặc điện thoại. Chỉ gửi mã đến thông tin đã đăng ký cho tài khoản sinh viên đang hoạt động; thông báo tiếp nhận chung tránh công khai tài khoản có tồn tại hay không. Tài khoản chưa đăng ký thông tin cần liên hệ học vụ.
3. Nhập mã 6 chữ số có hiệu lực 10 phút. Tối đa 5 lần thử, gửi lại sau 60 giây, tối đa 5 yêu cầu/địa chỉ/giờ và 10 yêu cầu/IP/15 phút. Giới hạn gửi mã được lưu trong DB, giữ qua lần khởi động lại. Gửi lại làm mất hiệu lực mã cũ của yêu cầu đó.
4. Đặt mật khẩu 10–128 ký tự gồm chữ cái và chữ số, xác nhận lại. Mật khẩu được băm Argon2; mọi mã khôi phục và phiên đăng nhập cũ bị thu hồi. Sinh viên đăng nhập lại với mật khẩu mới.

Mã xác minh được băm HMAC với khóa máy chủ và ID yêu cầu; DB không lưu mã thô, cookie chỉ giữ ID ngẫu nhiên và địa chỉ đã che. Có CSRF cho mọi POST. Nhật ký không lưu email, điện thoại, mật khẩu hay mã xác minh. Thay đổi thông tin khôi phục cần mật khẩu hiện tại, thu hồi yêu cầu khôi phục đang có và phiên trên các thiết bị khác. Thông tin liên hệ chỉ có trong API/hồ sơ của chính sinh viên.

## Cấu hình gửi thật

Sao chép các biến trong `.env.example` vào môi trường hoặc `.env` riêng (không đưa vào git), rồi khởi động lại server.

**Email:** đặt `EDUALERT_SMTP_HOST`, `EDUALERT_MAIL_FROM`, `EDUALERT_SMTP_USER`, `EDUALERT_SMTP_PASSWORD`. Mặc định cổng 587 với STARTTLS. Với SMTPS, đặt `EDUALERT_SMTP_SSL=true`, `EDUALERT_SMTP_PORT=465`. Máy chủ xác minh chứng chỉ TLS; thời gian chờ 10 giây. Có thể bỏ user/password với SMTP relay hỗ trợ STARTTLS và cho phép gửi theo địa chỉ máy chủ.

**SMS:** đặt `EDUALERT_SMS_URL` là endpoint HTTPS của gateway SMS do nhà trường vận hành, và `EDUALERT_SMS_TOKEN`. EduAlert gửi JSON `{"to":"+849...","message":"..."}` với header `Authorization: Bearer …`. Gateway phải chuyển tiếp tới nhà cung cấp SMS thực tế và chỉ trả 2xx sau khi nhà cung cấp chấp nhận. Không theo redirect để tránh gửi token sai đích. Đây là hợp đồng gateway, không phải tích hợp sẵn API của một nhà mạng cụ thể.

Chưa có nhà cung cấp hoặc thông tin xác thực được cấu hình trong repo này. Khi thiếu cấu hình hoặc dịch vụ từ chối, giao diện báo chưa thể gửi mã; không in mã ra console, không tạo đường tắt hay hiển thị thành công giả. Kiểm thử thay transport bằng bản ghi tạm riêng, không gửi email/SMS bên ngoài. Cần thử giao nhận bằng email/số điện thoại kiểm thử do đơn vị vận hành kiểm soát sau khi cấu hình để nghiệm thu việc gửi thật.

## Cập nhật cơ sở dữ liệu và chạy

Sao lưu DB bằng SQLite backup trước khi nâng cấp, sau đó chạy:

```powershell
./.venv312/Scripts/python.exe -m alembic upgrade head
./.venv312/Scripts/python.exe -m pytest tests/test_recovery.py -q
```

Migration `0003` bổ sung email/phone vào tài khoản sinh viên, phiên bản phiên đăng nhập và bảng yêu cầu khôi phục; giữ nguyên hồ sơ, tài khoản và mật khẩu hiện có. Khôi phục bản sao lưu nếu cần quay lại.

## Kết quả kiểm tra ngày 09/11/2026

- 61 kiểm thử hiện có đạt; 21 kiểm thử trong `tests/test_recovery.py` đạt; 6 kiểm thử JavaScript đạt. `node --check static/auth.js` và compile Python thành công. Còn một cảnh báo deprecation của Starlette/AnyIO.
- Đã tạo bản sao lưu SQLite trước migration `0003`. So sánh toàn bộ các cột cũ trong bảng users/students/student_accounts/course_results với bản sao lưu: không thay đổi, bao gồm password hash; `PRAGMA foreign_key_check` không có lỗi.
- Đã khởi động lại tại `http://127.0.0.1:8001`. `/health` trả `ok`, phiên bản `3.2.0`; đăng nhập, quên mật khẩu email/điện thoại và CSS/JS đều trả HTTP 200.

Kiểm tra giao diện: công cụ trình duyệt trong phiên chỉnh sửa bị dừng vì không xác định được URL Chrome trên Windows; chưa có nghiệm thu ảnh render desktop/mobile. HTML, route, CSRF, biểu mẫu và luồng backend được kiểm tra tự động; những kiểm tra này không thay thế quan sát bố cục trên trình duyệt.
