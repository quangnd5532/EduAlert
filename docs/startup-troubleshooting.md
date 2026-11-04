# Khi chưa mở được website

## Các nguyên nhân đã xác định trên máy hiện tại

1. Cấu hình F5 cũ trong `.vscode/launch.json` chỉ mở Chrome ở `localhost:8080`, không có tác vụ chạy backend. EduAlert dùng cổng8000. Đã sửa URL thành `http://127.0.0.1:8000`, thêm `preLaunchTask` chạy server và chỉ mở trang sau tín hiệu Uvicorn đã lắng nghe cổng.
2. Ban đầu công cụ chỉ nhận Python3.15 và `.venv` chỉ có pip. **Cập nhật04/11: log installer xác nhận Python3.12.10 đã cài thành công** ở `C:/Users/Quang/AppData/Local/Programs/Python/Python312`, kết quả0x0 lúc19:34. Công cụ bị Access is denied khi đọc đường dẫn mới nên kết luận “chưa cài” trước đó không đúng. Không cần cài lại; chạy script từ PowerShell thông thường với đường dẫn Python cụ thể bên dưới.
3. Tiến trình công cụ đang bị chặn kết nối Internet với `WinError10013`. Không tải được FastAPI, SQLAlchemy và các thư viện khác, cũng chưa tải Chart.js/Swagger UI. Kích hoạt virtualenv hoặc mở Chrome không giải quyết được việc thiếu thư viện.

## Khởi động lần đầu

Cài Python3.12 nếu `py -3.12 --version` chưa chạy được. Dùng [bộ cài trực tiếp Python3.12.10 x64 chính thức](https://www.python.org/ftp/python/3.12.10/python-3.12.10-amd64.exe), chọn Install Now; không chỉ tải Python Install Manager ở nút đầu trang phát hành. Không cần gỡ3.15. Sau cài, mở PowerShell mới tại thư mục dự án:

```powershell
py -3.12 --version
powershell.exe -NoProfile -ExecutionPolicy RemoteSigned -File .\start.ps1 -Demo
```

Script chọn Python, tạo môi trường riêng, cài phụ thuộc còn thiếu, tải tài nguyên local, migrate và seed. Lần seed đầu nếu chưa đặt `EDUALERT_DEMO_PASSWORD`, terminal yêu cầu tạo mật khẩu10–128ký tự; nội dung nhập không hiển thị. Mật khẩu này dùng cho `admin`, `advisor1`, `advisor2`. Lần sau seed không đổi mật khẩu hay nhân đôi dữ liệu.

Chỉ mở trình duyệt khi terminal hiện:

```text
Uvicorn running on http://127.0.0.1:8000
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

Nếu cổng8000 bận:

```powershell
.\start.ps1 -Demo -Port 8001
# Mở http://127.0.0.1:8001 (F5 vẫn dùng8000 theo cấu hình).
```

## Đọc đúng thông báo lỗi

| Thông báo | Ý nghĩa / bước xử lý |
|---|---|
| Không tìm thấy Python3.12/3.13 | Chưa có runtime mà script hỗ trợ; cài Python hoặc truyền -PythonExe. |
| Access is denied / không kiểm tra được quyền truy cập Python | Không được coi là chưa cài. Chạy từ terminal thông thường ngoài môi trường công cụ. Script hiện phân biệt lỗi này với đường dẫn không tồn tại. |
| `WinError10013`, `from versions: none` | Tiến trình không đọc được package index. Không có nghĩa phiên bản FastAPI đã pin không tồn tại. Cần môi trường cho phép kết nối PyPI và npm registry ở bước cài. |
| `No module named uvicorn` | Chưa cài xong thư viện vào đúng interpreter. Dùng script khởi động thay vì gọi `.venv`3.15 cũ. |
| `EDUALERT_ERROR: Migration...` | Chưa lên server; xem lỗi ngay phía trên, không tự xóa DB. |
| `address already in use` / lỗi cổng | Dừng server cũ hoặc chọn -Port8001; không dừng tùy tiện tiến trình khác. |
| Trình duyệt báo connection refused | Chưa có server lắng nghe tại đúng cổng; kiểm tra terminal trước. |

Không cần tắt firewall/antivirus hoặc giảm bảo vệ của máy. Nếu terminal bên ngoài công cụ cũng bị chặn tải, cần xử lý quyền mạng của môi trường hoặc cung cấp bộ wheel/tài nguyên offline từ nguồn tin cậy; hiện chưa có bộ offline trong repository.

## Những gì đã kiểm tra khi sửa launcher

Đã kiểm cú pháp PowerShell; chạy script trên máy hiện tại trả lỗi rõ ràng vì chưa có Python3.12/3.13. Truyền Python3.15 hiện có cũng được nhận diện đúng và từ chối dùng làm môi trường đích. JSON của VS Code task hợp lệ và regex khớp tín hiệu server đang lắng nghe. **Chưa chạy được server, toàn bộ quá trình bootstrap hoặc F5 thực tế**, vì chưa có runtime/phụ thuộc phù hợp và mạng của công cụ bị chặn.
