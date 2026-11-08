# Khi chưa mở được website

## Các nguyên nhân đã xác định trên máy hiện tại

1. Cấu hình F5 cũ chỉ mở Chrome ở `localhost:8080`, không có tác vụ chạy backend. **Bản3.1 dùng http://127.0.0.1:8001**, có `preLaunchTask` chạy server; server cũ ở8000 có thể vẫn giữ giao diện cũ.
2. Ban đầu công cụ chỉ nhận Python3.15 và `.venv` chỉ có pip. **Cập nhật04/11: log installer xác nhận Python3.12.10 đã cài thành công** ở `C:/Users/Quang/AppData/Local/Programs/Python/Python312`, kết quả0x0 lúc19:34. Công cụ bị Access is denied khi đọc đường dẫn mới nên kết luận “chưa cài” trước đó không đúng. Không cần cài lại; chạy script từ PowerShell thông thường với đường dẫn Python cụ thể bên dưới.
3. Ban đầu công cụ bị chặn mạng với `WinError10013`. **Cập nhật09/11:** `.venv312` đã có phụ thuộc và runtime3.12 cục bộ trong `.runtime/python312`; Chart.js/Swagger local đã có. Script nhận diện môi trường này và đã khởi động server3.1.0 thành công. Runtime cục bộ là phương án cho máy hiện tại, không được commit; trên máy sạch vẫn cài Python3.12/3.13 bình thường.

## Khởi động lần đầu

Cài Python3.12 nếu `py -3.12 --version` chưa chạy được. Dùng [bộ cài trực tiếp Python3.12.10 x64 chính thức](https://www.python.org/ftp/python/3.12.10/python-3.12.10-amd64.exe), chọn Install Now; không chỉ tải Python Install Manager ở nút đầu trang phát hành. Không cần gỡ3.15. Sau cài, mở PowerShell mới tại thư mục dự án:

```powershell
py -3.12 --version
powershell.exe -NoProfile -ExecutionPolicy RemoteSigned -File .\start.ps1 -Demo
```

Script chọn Python, tạo môi trường riêng, cài phụ thuộc còn thiếu, tải tài nguyên local, migrate và seed. Lần seed đầu nếu chưa đặt `EDUALERT_DEMO_PASSWORD`, terminal yêu cầu tạo mật khẩu10–128ký tự; nội dung nhập không hiển thị. Mật khẩu này dùng cho admin, cố vấn và sinh viên demo. Lần sau seed không đổi mật khẩu hay nhân đôi dữ liệu. Nếu đã có server3.1.0 tại cổng yêu cầu, script thông báo sẵn sàng và tái sử dụng.

Chỉ mở trình duyệt khi terminal hiện:

```text
Uvicorn running on http://127.0.0.1:8001
```

Giữ terminal đó chạy. Dừng bằng Ctrl+C. Cũng có thể dùng F5 với cấu hình Chrome hiện có; chú ý terminal tác vụ nếu cần nhập mật khẩu demo lần đầu.

Nếu cài Python ở đường dẫn riêng:

Python Install Manager có thể cài bản mới nhất (trên máy hiện tại là3.15) thay vì3.12. Cần cài đúng runtime3.12/3.13; chỉ cài trình quản lý chưa đủ. Script đã hỗ trợ cả thư mục `AppData/Local/Python/pythoncore-3.12-64` và `AppData/Local/Programs/Python/Python312`, kể cả khi launcher `C:/Windows/py.exe` cũ chưa nhận runtime mới.

```powershell
.\start.ps1 -PythonExe 'C:\duong-dan\Python312\python.exe' -Demo
```

Đường dẫn thực tế đã được xác nhận từ log cài đặt của máy này:

```powershell
cd C:\Users\Quang\Documents\EduAlert
powershell.exe -NoProfile -ExecutionPolicy RemoteSigned -File .\start.ps1 -PythonExe 'C:\Users\Quang\AppData\Local\Programs\Python\Python312\python.exe' -Demo
```

Nếu cổng8001 đang bị một ứng dụng khác chiếm:

```powershell
.\start.ps1 -Demo -Port 8002
# Mở http://127.0.0.1:8002 (F5 mặc định vẫn dùng8001).
```

## Đọc đúng thông báo lỗi

| Thông báo | Ý nghĩa / bước xử lý |
|---|---|
| Không tìm thấy Python3.12/3.13 | Chưa có runtime mà script hỗ trợ; cài Python hoặc truyền -PythonExe. |
| Access is denied / không kiểm tra được quyền truy cập Python | Không được coi là chưa cài. Chạy từ terminal thông thường ngoài môi trường công cụ. Script hiện phân biệt lỗi này với đường dẫn không tồn tại. |
| `WinError10013`, `from versions: none` | Tiến trình không đọc được package index. Không có nghĩa phiên bản FastAPI đã pin không tồn tại. Cần môi trường cho phép kết nối PyPI và npm registry ở bước cài. |
| `No module named uvicorn` | Chưa cài xong thư viện vào đúng interpreter. Dùng script khởi động thay vì gọi `.venv`3.15 cũ. |
| `EDUALERT_ERROR: Migration...` | Chưa lên server; xem lỗi ngay phía trên, không tự xóa DB. |
| `address already in use` / lỗi cổng | Dừng server mình đã mở hoặc chọn -Port8002; không dừng tùy tiện tiến trình khác. |
| Trình duyệt báo connection refused | Chưa có server lắng nghe tại đúng cổng; kiểm tra terminal trước. |

Không cần tắt firewall/antivirus hoặc giảm bảo vệ của máy. Nếu terminal bên ngoài công cụ cũng bị chặn tải, cần xử lý quyền mạng của môi trường hoặc cung cấp bộ wheel/tài nguyên offline từ nguồn tin cậy; hiện chưa có bộ offline trong repository.

## Những gì đã kiểm tra khi sửa launcher

Đã chạy `start.ps1 -Demo` thực tế: migration/nâng cấp dữ liệu và Uvicorn3.1.0 khởi động tại8001; chạy lại script nhận diện server và trả thông báo sẵn sàng. HTTP health/login/assets trả200. Toàn bộ61pytest và6test JavaScript đạt. Chưa thao tác F5 trực tiếp hoặc kiểm cài trên máy sạch khác. Công cụ trình duyệt báo “The browser access host is unavailable”, nên chưa nghiệm thu trực quan laptop/điện thoại; xem [testing.md](testing.md).
