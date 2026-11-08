# EduAlert — Hệ thống cảnh báo sớm học tập

Dự án giữa kỳ nhóm 5A: FastAPI + Jinja2 + SQLAlchemy + SQLite, giao diện tiếng Việt. Khối quản lý có 9 màn hình chính; cổng sinh viên có 6 trang riêng. Hồ sơ sinh viên và tài khoản cố vấn đều giả lập. Hai kết quả độc lập: xét điều kiện cảnh báo theo cấu hình và điểm ưu tiên hỗ trợ 0–100.

**Bản hiện tại 3.1.0 — 09/11/2026:** server đã chạy tại **http://127.0.0.1:8001**, đã migration/seed và phục vụ Chart.js/Swagger từ máy local. **61 kiểm thử pytest và 6 kiểm thử JavaScript chạy đạt**; còn 1 cảnh báo deprecation từ Starlette/AnyIO. Dữ liệu có 60 hồ sơ giả lập, 110 học phần, 2.676 kết quả học phần và 60 tài khoản sinh viên. Xem [cổng sinh viên và các trang riêng](docs/student-portal.md), [kết quả chạy kiểm tra](docs/release-checks.txt) và [giới hạn kiểm tra giao diện](docs/testing.md).

## Giới thiệu nhóm

| Thành viên | MSSV |
|---|---|
| Nguyễn Duy Quang | 2351010170 |
| Nguyễn Khánh Hưng | 2151010146 |
| Lê Hà Tấn Phong | 2451012074 |

Thông tin thật của thành viên chỉ dùng ở phần giới thiệu nhóm. Không dùng làm tài khoản cố vấn hay hồ sơ sinh viên demo.

## Cài và chạy trên Windows PowerShell

Khuyến nghị **Python 3.12 hoặc 3.13**. Bản hiện tại đã chạy bằng Python 3.12 với các phiên bản trong `requirements.txt`. Node có thể dùng để chạy kiểm thử frontend, không cần để chạy website. Cần mạng khi cài lần đầu; lúc chạy UI không gọi CDN.

```powershell
Set-Location C:\Users\Quang\Documents\EduAlert
py -3.12 --version
# Mật khẩu dưới đây CHỈ dùng với dữ liệu giả lập, không dùng trên hệ thống thật.
$env:EDUALERT_DEMO_PASSWORD = 'EduAlertDemo!2026'
powershell.exe -NoProfile -ExecutionPolicy RemoteSigned -File .\start.ps1 -Demo
```

Nếu chưa có Python3.12/3.13, cài trước theo [xử lý lỗi khởi động](docs/startup-troubleshooting.md). Script tự tìm runtime phù hợp và tạo `.venv312`/`.venv313`, giữ nguyên `.venv`3.15 cũ. Có thể truyền `-PythonExe` và `-Port`. Không đặt mật khẩu qua biến môi trường thì script hỏi trong terminal ở lần seed đầu. F5 của VS Code được cấu hình khởi động server rồi mở cổng8001; chưa thao tác F5 trực tiếp để nghiệm thu debugger. Script `start.ps1 -Demo` đã được chạy thực tế. Nếu cổng8001 đang chạy đúng bản3.1.0, script tái sử dụng server đó.

Lệnh thủ công, không cần activate:

```powershell
py -3.12 -m venv .venv312
./.venv312/Scripts/python.exe -m pip install -r requirements.txt
./.venv312/Scripts/python.exe scripts/vendor_assets.py
./.venv312/Scripts/python.exe -m alembic upgrade head
$env:EDUALERT_DEMO = 'true'
$env:EDUALERT_DEMO_PASSWORD = 'EduAlertDemo!2026'
./.venv312/Scripts/python.exe -m app.seed
./.venv312/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8001
```

Mở **http://127.0.0.1:8001**. Tài liệu API: **http://127.0.0.1:8001/docs**, schema **/openapi.json**. Nếu còn server cũ ở8000 thì có thể đang giữ mã cũ. Cài Chart.js 4.4.9 và Swagger UI 5.21.0 từ npm registry chính thức; script xác minh SRI SHA-512, chỉ lấy JS/CSS và giấy phép, lưu ở `static/vendor/`. Bước cài không cần Node/npm. Khi chưa có Chart.js, ứng dụng hiện thông báo và bảng số liệu thay thế. Swagger UI cũng cần assets cục bộ trước khi hiển thị.

| Tài khoản demo | Vai trò | Phạm vi |
|---|---|---|
| `admin` | Quản trị viên | Toàn bộ 60 hồ sơ |
| `advisor1` | Cố vấn A | L1, L2; 30 hồ sơ |
| `advisor2` | Cố vấn B | L3, L4; 30 hồ sơ |
| `student` hoặc `000005` | Sinh viên | Chỉ hồ sơ000005, cổng6 trang riêng |
| `sv000001`… hoặc mã SV | Sinh viên khác | Chỉ hồ sơ được liên kết với tài khoản |

Mật khẩu là giá trị `EDUALERT_DEMO_PASSWORD` **lúc seed lần đầu**, ví dụ `EduAlertDemo!2026` theo lệnh trên. Tài khoản sinh viên được tạo khi nâng cấp DB demo cũ dùng cùng mật khẩu admin demo lúc nâng cấp. Không có mật khẩu mặc định trong mã ứng dụng. Seed chạy lặp lại không nhân đôi, không tự đổi mật khẩu tài khoản cũ. Demo chỉ chạy khi `EDUALERT_DEMO=true`.

SQLite mới: `data/edualert-v2.db`; tệp khóa session local sinh ngẫu nhiên: `data/session.key`. Giữ hai tệp qua các lần khởi động; sao lưu DB khi ứng dụng dừng. `.env`, database và khóa không đưa vào git. Bản MVP cũ giữ trong `legacy/`; không tự chuyển dữ liệu cũ vào schema mới.

## Chạy trên Linux

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python scripts/vendor_assets.py
cp .env.example .env
export EDUALERT_DEMO=true
export EDUALERT_DEMO_PASSWORD='EduAlertDemo!2026'
.venv/bin/python -m alembic upgrade head
.venv/bin/python -m app.seed
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8001
```

## Kiểm thử

```powershell
# Chạy được chỉ với thư viện chuẩn:
./.venv312/Scripts/python.exe -m unittest tests.test_assessment tests.test_demo_data -v
# Nếu có Node (chỉ dùng cho kiểm thử, không bắt buộc khi chạy app):
node --test tests/frontend.test.cjs
# Sau khi cài phụ thuộc:
./.venv312/Scripts/python.exe -m pytest -q
./.venv312/Scripts/python.exe scripts/check_environment.py
# Hoặc: ./scripts/verify.ps1
```

pytest dùng SQLite tạm riêng theo từng test, seed dữ liệu giả lập, không sửa DB demo. Các test cũ nằm trong `legacy/` vì công thức/route đã thay đổi; `pytest.ini` chỉ chọn test hiện tại.

Nếu dùng Python3.13 thì thay `.venv312` bằng `.venv313`. Các test thuần Python vẫn có thể chạy bằng `.venv`3.15 cũ; API/DB cần môi trường đã cài đủ thư viện. `scripts/verify.ps1` tự ưu tiên `.venv312`/`.venv313`, hoặc nhận `-PythonExe`.

## Chức năng và tài liệu

- [9 giao diện và kiến trúc, ERD](docs/architecture.md)
- [Cổng sinh viên3.1: 6 trang riêng và luồng sử dụng](docs/student-portal.md)
- [Từ điển dữ liệu và quy ước tín chỉ](docs/data-dictionary.md)
- [Thuật toán, cấu hình và ví dụ tính tay](docs/algorithm.md)
- [Nhập CSV, quan hệ các mẫu](docs/csv.md) · [Tệp mẫu](samples/)
- [Danh sách route, API và quyền](docs/routes.md)
- [Báo cáo dự án](docs/project-report.md)
- [Kịch bản demo 7–10 phút](docs/demo-script.md)
- [Câu hỏi giảng viên và đề xuất phân công](docs/defense.md)
- [Bằng chứng kiểm thử và checklist thủ công](docs/testing.md)
- [Xử lý lỗi khởi động, Python và F5](docs/startup-troubleshooting.md)

## Lưu ý triển khai

Giữ `EDUALERT_HTTPS=false` cho local HTTP. Khi triển khai sau reverse proxy HTTPS, đặt `EDUALERT_HTTPS=true` và `EDUALERT_SECRET` ngẫu nhiên ít nhất 32 ký tự qua biến môi trường. Cookie session HttpOnly, SameSite=Lax, Secure khi bật HTTPS. Session chứa ID và CSRF, không chứa hồ sơ học tập. Mọi ghi dữ liệu cần CSRF, mọi truy cập sinh viên kiểm tra phân công ở backend.

Bản này phục vụ demo cục bộ, chưa kiểm định production. Chưa có khôi phục mật khẩu, nhiều cơ sở đào tạo, quy chế học lại, mô hình dự đoán hay gửi thông báo tự động. GPA tích lũy giả định chỉ tính khi có GPA hiện tại, số tín chỉ đã tính GPA và xác nhận không học lại/mọi tín chỉ kỳ tới tính GPA; thiếu điều kiện thì hiện lý do. Không có tuyên bố về độ chính xác dự đoán hoặc hiệu quả nhân quả của can thiệp.
