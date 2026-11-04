# EduAlert — Nhóm 5A

MVP hệ thống cảnh báo sớm học tập bằng **Python / FastAPI + SQLite**, giao diện tiếng Việt responsive bằng HTML/CSS/JavaScript. Không cần Node hoặc npm để chạy.

Thành viên: Nguyễn Duy Quang — 2351010170; Nguyễn Khánh Hưng — 2151010146; Lê Hà Tấn Phong — 2451012074.

## Khởi chạy trên Windows

Cần Python (khuyến nghị 3.12 hoặc 3.13) và kết nối Internet để cài thư viện lần đầu. Trong PowerShell tại thư mục dự án:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Mở **http://127.0.0.1:8000**. Tài liệu API tương tác: **http://127.0.0.1:8000/docs**. Có thể chạy `./start.ps1` để thực hiện các bước tự động nếu máy cho phép chạy script. Không cần activate môi trường ảo.

Lần đầu danh sách trống: chọn **Khám phá với 24 hồ sơ minh họa**, hoặc tải mẫu ở **Nhập dữ liệu** và nhập CSV. Không tự thêm dữ liệu giả vào danh sách thật. SQLite lưu tại `data/edualert.db`, tồn tại sau khi khởi động lại; sao lưu tệp này khi dừng máy chủ.

Nếu chưa cài được thư viện, mở **preview.html** trực tiếp bằng trình duyệt để xem trước 9 màn hình với dữ liệu mẫu. Bản xem trước chỉ đọc, không lưu biểu mẫu, không nhập/xuất CSV. Tạo lại bản xem trước sau khi sửa frontend bằng `py scripts/build_preview.py`.

## 9 màn hình

1. Tổng quan: thống kê, xu hướng GPA, phân bố nguy cơ và danh sách ưu tiên.
2. Sinh viên: tìm kiếm không dấu, lọc lớp/ngành/khóa/nguy cơ, phân trang, thêm sinh viên.
3. Hồ sơ sinh viên: GPA qua từng kỳ, điểm tuyển sinh và thang điểm, lý do cảnh báo, điều kiện quy chế, lịch sử can thiệp.
4. Kết quả học tập: nhập hoặc sửa điểm và tín chỉ từng học kỳ.
5. Cảnh báo sớm: danh sách cần chú ý/nguy cơ cao, điểm số và kết quả quy chế riêng.
6. Theo dõi can thiệp: ghi chú, biện pháp, cố vấn, lịch hẹn, trạng thái, kết quả và xuất CSV.
7. Nhập dữ liệu: tải mẫu, kiểm tra toàn bộ tệp trước khi lưu, báo dòng lỗi.
8. Báo cáo & thống kê: thống kê lớp/ngành, xuất CSV UTF-8 mở bằng Excel.
9. Cấu hình: phạm vi khóa, ngưỡng quy chế, trọng số nguy cơ, ranh giới phân loại; lưu để tính lại.

## Quy tắc minh họa, không phải quy chế của trường

Hai kết quả độc lập. Cảnh báo học vụ: GPA kỳ < 1.2 **hoặc** GPA tích lũy < 1.8 **hoặc** tỷ lệ tín chỉ không đạt ≥ 50%. Màn hình chỉ ghi nhận điều kiện, không ban hành quyết định.

Điểm nguy cơ: GPA kỳ < 2.0 (+30), GPA giảm liên tiếp ở 3 kỳ đã nhập (+25), tín chỉ không đạt tăng so với kỳ đã nhập trước (+20), đã có cảnh báo trước kỳ đang xét (+15), rèn luyện < 50/100 (+10). Tổng tối đa 100; 0–29 bình thường, 30–59 cần chú ý, ≥60 nguy cơ cao. Các ngưỡng/trọng số có thể chỉnh. Kỳ thiếu trong dữ liệu không được nội suy; xu hướng so sánh các kỳ đã nhập theo thứ tự năm/học kỳ. Thiếu rèn luyện thì không cộng điểm yếu tố đó. Thiếu toàn bộ học kỳ hiển thị **Chưa có dữ liệu**, ngoài phạm vi khóa hiển thị **Ngoài phạm vi**, không coi là bình thường.

GPA tích lũy do người dùng cung cấp, không tự tính từ GPA kỳ vì thiếu điểm và tín chỉ từng học phần. Điểm tuyển sinh không đưa vào công thức nguy cơ do khác phương thức/thang điểm. `debt` là số học phần còn nợ; `previous_warnings` là số cảnh báo trước học kỳ đó, được nhập từ lịch sử đã xác nhận.

## CSV

Tải mẫu từ `/api/import/template`. Mỗi dòng là một sinh viên/học kỳ. Tối đa 2 MB / 5.000 dòng, UTF-8 có hoặc không BOM, dấu phẩy phân cách, dấu chấm thập phân. Tín chỉ đạt + không đạt = tín chỉ đăng ký. GPA từ 0 đến 4, rèn luyện từ 0 đến 100; GPA tích lũy và các giá trị tín chỉ là bắt buộc. Điểm tuyển sinh/rèn luyện có thể để trống. Không sửa tên cột.

Khóa cập nhật: mã sinh viên + năm + học kỳ. CSV cập nhật thông tin sinh viên cùng mã và thay thế học kỳ cùng khóa; không xóa các kỳ khác. Trong một tệp, không được trùng khóa hoặc có thông tin cá nhân mâu thuẫn giữa các dòng. Có bất kỳ dòng lỗi thì toàn bộ giao dịch không lưu. Xuất CSV có BOM và xử lý chuỗi bắt đầu bằng dấu công thức để hạn chế spreadsheet formula injection.

## Kiểm tra

```powershell
py -m unittest discover -s tests -p test_risk.py -v
.\.venv\Scripts\python.exe -m pytest -q
```

Unit tests cho thuật toán không cần thư viện ngoài. API tests dùng cơ sở dữ liệu tạm riêng; kiểm tra khởi tạo mẫu, CRUD, CSV không lưu một phần, upsert, xác thực dữ liệu, xuất báo cáo. Không chạm `data/edualert.db`.

## Phạm vi MVP

Chạy local một không gian cố vấn; **chưa có đăng nhập, phân quyền, nhật ký kiểm toán hoặc triển khai production**. Không đưa bản này lên Internet với dữ liệu thật. Hiện hỗ trợ một bộ quy tắc hoạt động cho tất cả khóa hoặc một khóa; bộ quy tắc nhiều trường/nhiều khóa đồng thời cần mở rộng. Chưa có danh mục từng học phần nợ, chỉ lưu số lượng. GPA và điểm nguy cơ là thống kê theo quy tắc giải thích được, không phải mô hình ML hoặc kết luận tự động về sinh viên.

Frontend được FastAPI phục vụ cùng origin, không cần CORS. Cách mount tài nguyên theo [tài liệu chính thức FastAPI](https://fastapi.tiangolo.com/tutorial/static-files/).
