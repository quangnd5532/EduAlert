# Giao diện và API

FastAPI docs: `/docs`, OpenAPI JSON: `/openapi.json`. Schema input lấy từ Pydantic. Một số response dùng dict thay vì response model riêng để cấu trúc đồ án gọn; mã và dữ liệu thực tế là nguồn tham chiếu cho response chi tiết.

## Giao diện HTML

| Method | Route | Quyền |
|---|---|---|
| GET/POST | /login | Khách; POST cần CSRF phiên login |
| POST | /logout | Có CSRF; xóa session |
| GET | /dashboard | Admin / cố vấn trong phạm vi |
| GET | /students | Admin / cố vấn trong phạm vi |
| GET | /students/{sid} | Kiểm tra phân công, ngoài quyền trả404 |
| GET | /import | Admin |
| GET | /settings | Admin |
| GET | /interventions | Admin / cố vấn trong phạm vi |
| GET | /reports | Admin / cố vấn trong phạm vi |
| GET | /admin | Admin |
| GET | / | Chuyển tới dashboard |

## JSON / CSV

Mọi thao tác thay đổi cần header `X-CSRF-Token` lấy từ meta csrf-token của trang sau đăng nhập, hoặc hidden csrf của form urlencoded. Swagger không tự điền token: sau đăng nhập cùng trình duyệt, điền token ở trường X-CSRF-Token của endpoint cần ghi. GET có thể thử cùng session. Swagger UI 5.21.0 dùng JS/CSS cục bộ được cài qua `scripts/vendor_assets.py`, không gọi CDN. Khi chưa cài assets, `/openapi.json` vẫn đọc được nhưng Swagger chưa render được.

| Method | Endpoint | Dữ liệu / chức năng | Quyền |
|---|---|---|---|
| GET | /health | Version và process alive (không xác nhận DB) | Public |
| GET | /api/students | items, total, page, pages, semester_id | Scoped |
| POST | /api/students | StudentInput; tạo mới | Admin |
| PUT | /api/students/{sid} | StudentInput; cập nhật hồ sơ/phân công, giữ mã | Admin |
| GET | /api/students/{sid} | Hồ sơ, dữ liệu, đánh giá hiện tại, chart, snapshot, can thiệp | Scoped resource |
| PUT | /api/results | ResultInput; tạo/cập nhật kỳ | Admin |
| POST | /api/students/{sid}/evaluate?semester_id=6 | Lưu snapshot hoặc tái dùng bản tương đương gần nhất | Scoped resource |
| POST | /api/students/{sid}/simulate?semester_id=6 | GPA, registered, failed; before/after, không lưu | Scoped resource |
| GET | /api/summary | Tổng, đủ/thiếu, các mức, hồ sơ mở/quá hạn, ưu tiên | Scoped |
| GET | /api/trend | Thống kê từng kỳ chính đến kỳ lọc, cấu hình hiện hành | Scoped |
| GET | /api/report-groups | Nhóm theo class_id, major_id, cohort_id | Scoped |
| GET | /api/export | CSV toàn bộ tập lọc, không chỉ trang hiện tại | Scoped |
| GET | /api/interventions | Hồ sơ trong phạm vi và ghi chú | Scoped |
| POST | /api/interventions | Gắn sinh viên, evaluation_id; mục tiêu, biện pháp, ngày hẹn | Scoped resource |
| PATCH | /api/interventions/{pid} | Trạng thái, note, tùy chọn mục tiêu/biện pháp/ngày hẹn | Scoped resource |
| GET | /api/configs | Các phiên bản/payload | Admin |
| POST | /api/configs | Tạo bản nháp đã kiểm tra | Admin |
| POST | /api/configs/{id}/preview | Số đổi mức, thiếu dữ liệu ở kỳ chính mới nhất | Admin |
| POST | /api/configs/{id}/activate | Kích hoạt trong phạm vi, giữ lịch sử | Admin |
| GET | /api/import/template/{kind} | CSV mẫu students/results/debts/warnings | Admin |
| POST | /api/import/preview | multipart: file, kind, mode skip/update | Admin |
| POST | /api/import/{bid}/confirm | Kiểm tra lại, ghi cả lô, đánh consumed | Admin + chủ batch |
| GET | /api/import/{bid}/errors | CSV lỗi preview | Admin + chủ batch |
| POST | /api/accounts | username, name, password; tạo advisor | Admin |
| PATCH | /api/accounts/{uid} | active true/false, chỉ cố vấn | Admin |
| POST | /api/catalog/{kind} | Upsert majors/cohorts/classes/courses; tạo semesters mới | Admin |

`Scoped` nghĩa admin toàn cục, cố vấn chỉ sinh viên có students.advisor_id = user.id. Thống kê can thiệp lấy sinh viên hiện được phân công, không dựa vào owner_id lịch sử để mở rộng quyền.

## Query filter dùng chung

`semester_id`, `q` (tìm tên/mã không phân biệt hoa thường, **không** tự bỏ dấu), `class_id`, `major_id`, `cohort_id`, `level` (nhãn tiếng Việt), `rule` (true/false/unknown/none), `status` (4 trạng thái tiếng Việt), `sort` (risk/name/id). `page` chỉ áp dụng danh sách, 12 dòng/trang; xuất CSV không phân trang. Không tin tham số advisor từ client. Bộ lọc được lưu trong URL trang danh sách/dashboard/báo cáo để tải lại và xuất dùng cùng giá trị.

Khi lọc mức nguy cơ hoặc kết quả quy tắc trong biểu đồ diễn biến, bộ lọc được áp dụng riêng theo mỗi kỳ (không phải một đoàn hệ cố định của kỳ cuối). Nhãn hiện hành có thể khác snapshot cũ, xem lịch sử riêng ở hồ sơ.

## Lỗi

401 chưa đăng nhập (HTML chuyển tới login); 403 không có quyền hoặc sai CSRF; 404 không tồn tại/ngoài phân công; 409 trùng dữ liệu hoặc batch đã nhập; 410 phiên preview hết hạn; 422 input không hợp lệ; 429 giới hạn thử đăng nhập. Không trả mật khẩu/hash trong các endpoint danh sách hoặc trang quản trị.
