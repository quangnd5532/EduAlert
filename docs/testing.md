# Báo cáo kiểm thử thực tế và checklist

## Kết quả hiện tại — 09/11/2026, bản3.1.0

Đã chạy `./.venv312/Scripts/python.exe scripts/check_release.py` trên Python3.12. Nhật ký đầy đủ: [release-checks.txt](release-checks.txt).

| Kiểm tra đã chạy | Kết quả quan sát |
|---|---|
| Compile Python | Thành công |
| Toàn bộ pytest: công thức, DB/API, quyền, CSV, phiên bản, can thiệp, dữ liệu và cổng sinh viên | **61 passed** trong44,74giây |
| `node --check static/student.js` | Thành công |
| `node --test tests/frontend.test.cjs` | **6 passed**,0fail |
| `start.ps1 -Demo`, migration/nâng cấp dữ liệu và Uvicorn | Server3.1.0 khởi động tại127.0.0.1:8001 |
| HTTP `/health`, `/login`, CSS/JS sinh viên, CSS đăng nhập, Chart.js local |200; health trả version3.1.0 |
| GET `/student/results` khi chưa đăng nhập |303 về đăng nhập |

Pytest còn **1 DeprecationWarning** từ Starlette TestClient sử dụng alias `anyio.abc.BlockingPortal`. Đây là cảnh báo thư viện trong test, không phải lỗi làm server ngừng chạy; không tắt cảnh báo để che kết quả.

Các test cổng sinh viên kiểm6trang riêng, điều hướng giữ học kỳ, HTML có dữ liệu sẵn, biểu mẫu chỉ xuất hiện ở trang đúng chức năng, POST có CSRF khi không có JavaScript, yêu cầu tư vấn lưu thật, lọc bảng điểm và CSV khớp, chặn quyền, mô phỏng không ghi dữ liệu thật, tên kỳ hè và đối soát GPA từng học phần. Mô phỏng kiểm cả giá trị GPA tích lũy giả định trong điều kiện quy tắc.

**Chưa xác minh trực quan:** công cụ trình duyệt trả lỗi **“The browser access host is unavailable”** trong lần kiểm tra09/11. Chưa có bằng chứng đủ để kết luận luồng click qua trình duyệt, render Chart.js, layout laptop/điện thoại và debugger F5 đã đạt. Kiểm tra HTML/API/Node không thay thế các thao tác đó. Checklist bên dưới vẫn dùng cho kiểm tra thủ công. Cài trên một máy Windows sạch khác và triển khai HTTPS chưa được chạy thử.

## Lịch sử kiểm tra ban đầu — 02–03/11/2026

Phần dưới được giữ làm lịch sử tại thời điểm chưa có môi trường chạy; các dòng “chưa chạy” trong phần lịch sử không mô tả trạng thái3.1.0 ở trên.

Ngày thực hiện: **02–03/11/2026**, môi trường Windows PowerShell tại thư mục EduAlert. Python đang có: **3.15.2**; virtualenv chỉ có pip. Lần tiếp tục ngày03/11 có Node **26.13.0** để kiểm thử JavaScript. Bộ ứng dụng khuyến nghị Python3.12/3.13.

## Đã thực sự chạy

| Lệnh / thao tác | Kết quả quan sát |
|---|---|
| Đọc repo và kiểm tra môi trường | Có MVP cũ; đã giữ ở legacy/, dùng DB v2 riêng |
| `python -m unittest tests.test_assessment tests.test_demo_data -q` (qua .venv) | **34 test, OK** (28 thuật toán + 6 dữ liệu demo) |
| `node --check static/portal.js` | Thành công, không lỗi cú pháp JavaScript |
| `node --test tests/frontend.test.cjs` | **6 test, pass6, fail0**, dùng DOM/API giả lập, không phải browser E2E |
| `python -m compileall -q app migrations scripts tests` | Thành công; không phát hiện lỗi cú pháp Python |
| `python scripts/create_samples.py` | Sinh 6 tệp CSV UTF-8 BOM giả lập |
| `pip install ...` các phụ thuộc, thử lại03/11 | Thất bại: kết nối PyPI bị chặn, WinError10013; không có thư viện cài sẵn/cache. Thông báo “from versions: none” bắt nguồn từ không đọc được index, không phải bằng chứng phiên bản không tồn tại. |
| `python scripts/vendor_assets.py` | Thất bại: kết nối npm registry bị chặn, WinError10013; chưa có Chart.js local |
| `python -m pytest -q` | Không khởi động được: `No module named pytest`; **không có kết quả pass cho integration** |
| `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000` | Khởi động bị chặn do `No module named uvicorn`; không có server ứng dụng đang chạy |
| `python scripts/check_environment.py` | Báo thiếu thư viện ứng dụng và Chart.js |
| Khám phá browser bằng cua.getState | `The browser access host is unavailable`; chưa có phiên browser điều khiển được |
| Thử lại công cụ browser ngày03/11 | Không khởi tạo được Node runtime của công cụ: `The system cannot find the path specified` (os error3), dù Node CLI kiểm thử chạy được |

Không tuyên bố FastAPI đã khởi động thành công, DB/migration/seed đã chạy, hay UI laptop/mobile đã được kiểm tra. Không có ảnh chụp giao diện render để làm bằng chứng nghiệm thu. Không có số liệu accuracy/F1 vì đây không phải mô hình dự đoán đã huấn luyện. Việc review giao diện theo skill chưa thể hoàn tất khi không render được runtime.

Đầu ra kiểm tra có thể tái tạo bằng `python scripts/run_available_checks.py`, được lưu ở [available-checks.txt](available-checks.txt). Script này không thay thế pytest tích hợp hoặc kiểm tra trình duyệt.

## Kiểm thử không cần server đã đạt

28 test thuật toán: ví dụ tính tay71.5 và từng contribution; mốc30/60; clamp GPA/tín chỉ; thiếu GPA;0 đăng ký; GPA ngoài khoảng/NaN/Infinity; tín chỉ sai tổng; thiếu kỳ giữa; nghỉ học; kỳ giữa chưa hoàn thành không được bỏ qua; thiếu3 kỳ; GPA bằng nhau/tăng; bỏ kỳ hè; input không sắp thứ tự; không dùng tương lai; đúng cửa sổ3 cảnh báo; xác nhận false khác thiếu dòng; thiếu cấu hình; OR/AND ba trạng thái; từ chối trường/toán tử không an toàn; tổng trọng số; mẫu số0; thứ tự ngưỡng; mô phỏng không sửa input; cấu hình sai hình dạng.

6 test dữ liệu demo dùng chính `academic_data()` mà CLI seed sử dụng: kiểm tín chỉ/khóa kỳ của60 hồ sơ, trường hợp ổn định,71.5 nhưng rule false, thiếu dữ liệu, không đạt/lặp lại cao và cải thiện qua kỳ. **Đây chưa phải kiểm thử ghi DB bằng lệnh seed.**

6 test frontend chạy mã `portal.js` thật trong Node vm với DOM/API giả: escape HTML ở danh sách và can thiệp; phân biệt kết quả A/B, cấu hình/thời điểm/chưa lưu; quá hạn và so sánh trước/sau; CSRF/JSON/lỗi tại trường; cùng bộ lọc summary/trend và mẫu số thiếu dữ liệu; trạng thái rỗng/nhóm OR unknown. Không xác minh layout, sự kiện DOM thật, Chart.js hay kết nối API thực.

## Kiểm thử tích hợp đã viết, chưa chạy

`tests/test_application.py` có **14 test** (trong đó một test helper CSV injection không cần DB nhưng vẫn nằm trong suite pytest cần cài phụ thuộc). Fixture riêng SQLite tạm/seed60 sinh viên mỗi test. Bao phủ:

- Đăng nhập/cookie/CSRF, danh sách60, cố vấn30; chặn đọc/sửa/mô phỏng/đánh giá/xuất sinh viên ngoài phân công; chặn cấu hình và trang admin.
- Cả9 route giao diện và tài liệu OpenAPI trả200 sau đăng nhập.
- Tạo nháp, preview, kích hoạt, ưu tiên phạm vi, giữ evaluation cũ/cấu hình cũ.
- Mô phỏng before/after và số lượng bảng dữ liệu thật không đổi; GPA không hợp lệ trả422; GPA tích lũy giả định chỉ tính khi đủ giả định được xác nhận.
- Lưu can thiệp, trạng thái, ghi chú, quá hạn và cố vấn khác không sửa được.
- CSV BOM, lỗi ngăn cả lô, duplicate nội bộ/DB, skip/update, confirm một lần, revalidate sau preview, GPA sai không đổi dữ liệu.
- Bảng/summary/trend/CSV cùng số dòng theo bộ lọc; chống CSV formula injection.
- Seed lặp lại không nhân đôi.

Đây là **test được viết**, không phải danh sách đã pass. Cần cài phụ thuộc và chạy toàn bộ suite, sửa lỗi phát hiện trước khi bảo vệ bài.

## Checklist nghiệm thu sau khi có môi trường

Đánh dấu theo quan sát thực tế, không đánh dấu sẵn:

- [ ] Python3.12/3.13, pip install, vendor_assets thành công; tắt mạng rồi kiểm tra UI và biểu đồ vẫn hoạt động.
- [ ] Alembic upgrade trên DB trống, seed một lần60 hồ sơ; seed lại vẫn60; restart giữ dữ liệu.
- [ ] Chạy pytest, ghi số pass/fail thật và phiên bản Python/thư viện.
- [ ] Đăng nhập admin; kiểm tra tên và role trên topbar; sai mật khẩu hiện lỗi tiếng Việt.
- [ ] Advisor1 thấy30 hồ sơ; truy cập URL và API000003 trả404; export không có000003; import/settings/admin trả403.
- [ ] Dashboard lọc kỳ6, ngànhCNTT, khóaK23, lớpL1; số bảng/phân bố/CSV khớp; chưa đủ dữ liệu không gộp bình thường.
- [ ] Danh sách tìm000005, vào hồ sơ, tab giải thích có71.5 và quy tắc không thỏa.
- [ ] Biểu đồ GPA có đơn vị4, không đạt% và nguy cơ100, tooltip/chú giải; SV000007 có khoảng trống và nhãn thiếu dữ liệu.
- [ ] Mô phỏng000005 với GPA3,20 đăng ký,0 không đạt:15 điểm. Reset khôi phục3 trường về giá trị ban đầu của form. Quay lại học tập vẫn giữ GPA1.9/tín chỉ8 không đạt.
- [ ] Tạo can thiệp mới; trạng thái Chưa xử lý; cập nhật Đang hỗ trợ/Chờ theo dõi và ghi chú; reload vẫn còn. Ngày hẹn cũ hiện quá hạn, hoàn tất không còn quá hạn.
- [ ] Hồ sơ000006 hiển thị mốc đánh giá kỳ4 GPA1.6 và kỳ5 tiếp theo2.3; không có khẳng định nhân quả.
- [ ] Đăng nhập admin, preview students_errors, thấy dòng/cột/hướng sửa, tải lỗi; không thêm sinh viên. Nhập mẫu hợp lệ theo thứ tự, confirm rồi thấy009001.
- [ ] Preview CSV trùng, chọn skip/update rõ ràng; lỗi trong lô không lưu dòng hợp lệ trước đó.
- [ ] Lưu cấu hình nháp với trọng số tổng sai bị từ chối; nháp hợp lệ không áp dụng ngay; preview có số đổi mức/thiếu; activate rồi snapshot cũ vẫn phiên cũ.
- [ ] Tạo ngành/khóa/lớp/học phần/học kỳ mới, tạo/khóa/mở cố vấn, đổi phân công; quyền cũ bị thu hồi ngay.
- [ ] Báo cáo theo lớp/ngành/khóa, CSV giữ số0 đầu; print PDF không có sidebar/form nút và không cắt mất cột.
- [ ] Thử tab/shift-tab, enter submit, arrow/home/end trên tab hồ sơ; focus dễ thấy. Kiểm tra thông báo lỗi, rỗng và đang tải.
- [ ] Ở laptop1440×900 và điện thoại390×844: không tràn toàn trang; bảng cuộn riêng, nav cuộn ngang, form một cột, nút không che nội dung.
- [ ] DevTools không có JS error; mọi request cùng origin; không có CDN trong UI nghiệp vụ và Swagger. Cần cài cả Chart.js và Swagger UI vào static/vendor trước.

## Rủi ro còn lại

Cập nhật04/11: đã đọc log installer Python3.12.10 với `Apply complete, result: 0x0` và đường dẫn cài `AppData/Local/Programs/Python/Python312`. Khi thử đọc/chạy đường dẫn đó bằng công cụ, hệ thống trả `Access is denied`; đây là hạn chế quyền của tiến trình, không phải bằng chứng Python chưa cài. Đã sửa launcher để thông báo riêng lỗi quyền. Đã chạy lại34 test Python thuần và6 test JavaScript, đều đạt; kiểm thử tích hợp/server vẫn chưa chạy được.

Đã sửa launcher sau phản hồi chưa chạy được web: cấu hình VS Code cũ mở8080 và không chạy backend; nay dùng preLaunchTask, cổng8000 và đợi tín hiệu Uvicorn lắng nghe. `start.ps1` chọn Python3.12/3.13, tạo venv riêng, giữ `.venv`3.15, hỗ trợ -PythonExe/-Port/-Demo và hỏi mật khẩu ở lần seed đầu nếu thiếu. Đã kiểm cú pháp PowerShell và regex readiness; chạy launcher hiện dừng với thông báo chưa có runtime phù hợp. Chưa xác minh trọn luồng bootstrap hoặc F5 thực tế. Chi tiết ở [startup-troubleshooting.md](startup-troubleshooting.md).

Chưa xác minh khả năng tương thích các phụ thuộc đã pin trên Python đích, behavior SQLAlchemy transaction trong import/activation, render Jinja2, chạy migration Alembic và JavaScript/Chart.js trong trình duyệt. Các phần này cần kiểm thử tích hợp thật, không thể suy ra từ compileall. Script khởi động dừng khi install/vendor/migration/seed lỗi để tránh hiểu nhầm đã chạy thành công.
