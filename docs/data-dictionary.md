# Từ điển dữ liệu

Quy ước: ID sinh viên là **chuỗi**, ví dụ `000005`; không ép sang số. Số thực GPA ở thang 4, không chấp nhận NaN/Infinity. Học kỳ dùng `sequence` độc lập với ID để sắp thứ tự; tên kỳ chỉ để trình bày. Các trường `created_at` dùng thời điểm UTC; ngày hẹn dùng ngày local của máy chủ (demo Asia/Bangkok).

| Bảng | Trường và ý nghĩa |
|---|---|
| `users` | `id`, `username` duy nhất; `name` tên hiển thị; `password_hash` Argon2; `role` admin/advisor/student; `active` khóa/mở. Không lưu mật khẩu thô. |
| `student_accounts` | `user_id` khóa chính/FK users; `student_id` duy nhất/FK students. Liên kết một tài khoản sinh viên với đúng một hồ sơ. |
| `majors` | `id`, `name` danh mục ngành. |
| `cohorts` | `id`, `name` khóa tuyển sinh, demo K22/K23. |
| `classrooms` | `id`, `name`; `major_id`, `cohort_id`. Sinh viên lấy ngành/khóa từ lớp, không lặp cột ngành/khóa trong student. |
| `semesters` | `id` khóa tham chiếu; `name`; `sequence` duy nhất, tăng theo thời gian; `kind` regular/summer; `completed` chỉ kỳ đã hoàn thành mới xét. |
| `students` | `id`, `name`, `class_id`, `advisor_id`; `admission_score` điểm đầu vào, `admission_scale` thang điểm, `admission_method` phương thức. Điểm có giá trị cần cả phương thức và thang; không so sánh xuyên thang. |
| `academic_results` | `id`, `student_id`, `semester_id` cặp duy nhất; GPA/tín chỉ bên dưới; `status` completed/leave. |
| `courses` | `id`, `name`, `credits` số tín chỉ học phần. Điểm nằm ở course_results; chưa mô hình hóa nhiều lần thi trong cùng kỳ. |
| `course_results` | `id`; `student_id`, `semester_id`, `course_id` bộ ba duy nhất; `grade` thang4 hoặc NULL chờ điểm. Dữ liệu demo dùng0 cho F/không đạt,1trở lên cho điểm đạt; đây không phải quy chế một trường cụ thể. |
| `debts` | `student_id`, `semester_id`, `course_id` bộ ba duy nhất; snapshot **các học phần bắt buộc còn phải hoàn thành** tại kỳ. Có thể lặp lại ở kỳ sau nếu chưa trả nợ. |
| `warning_history` | `student_id`, `semester_id` duy nhất; `warned=true` đã có cảnh báo, `false` đã xác nhận không cảnh báo. Không có dòng là chưa biết, không phải false. Đây là lịch sử quyết định giả lập được nhập, không tự coi kết quả rule engine là quyết định đã ban hành. |
| `config_versions` | `id`, `name`; `major_id`/`cohort_id` NULL = không giới hạn; `payload` JSON tham số + cây điều kiện; `active`, `activated_at` lần kích hoạt gần nhất, `created_at`. Bản chưa kích hoạt là nháp; bản từng kích hoạt đã tắt là phiên cũ. |
| `evaluations` | `student_id`, `semester_id`, `config_id` có thể NULL nếu chưa có cấu hình; `input_data` snapshot dữ liệu được dùng; `output` JSON điểm, lý do, trạng thái; `created_at`. Cho phép nhiều lần đánh giá khi input hoặc cấu hình thay đổi. |
| `interventions` | `student_id`, `evaluation_id` mốc đánh giá; `owner_id` cố vấn lúc tạo; `goal`, `action`, `status`, `due_date`, `created_at`. Ngày hẹn là lịch hẹn hiện tại của hồ sơ, không có bảng lịch tái diễn. |
| `followups` | `intervention_id`, `author_id`, `note`, `created_at` ghi chú nối tiếp, không ghi đè ghi chú trước. |
| `audit_logs` | `user_id`, `action`, `detail` JSON không chứa bí mật, `created_at`. |
| `import_batches` | ID ngẫu nhiên, chủ sở hữu, loại mẫu, chế độ skip/update, các dòng gốc, lỗi preview, cờ consumed, thời điểm tạo; phiên xác nhận hết hạn sau 1 giờ. |

## Định nghĩa kết quả học tập và tín chỉ

| Trường | Định nghĩa và ràng buộc |
|---|---|
| `gpa` | GPA học kỳ đã được hệ thống nguồn tổng hợp trên thang 4. NULL = chưa có; 0 là giá trị hợp lệ, khác NULL. |
| `cumulative_gpa` | GPA tích lũy đến cuối kỳ theo dữ liệu nguồn; không tự lấy trung bình GPA các kỳ trong ứng dụng thật. Demo tổng hợp theo tổng điểm có trọng số tín chỉ của các môn đã có điểm tới kỳ xét, có giả định không học lại; không dùng điểm này để suy quy chế học lại. |
| `registered` | Tín chỉ đã được chốt kết quả trong học kỳ; không bao gồm môn đang chờ điểm/hủy đăng ký. Tên hiển thị “tín chỉ đăng ký” theo yêu cầu; mẫu demo giả định mọi tín chỉ đăng ký đã chốt kết quả. 0–60. |
| `passed` | Tín chỉ có kết quả đạt trong kỳ, 0–60. Có thể gồm học lại đã đạt; không mặc nhiên là tín chỉ mới tích lũy. |
| `failed` | Tín chỉ không đạt trong kỳ, 0–60; `passed + failed = registered`. Dùng đúng tỷ lệ `failed / registered`, không dùng tổng nợ thay thế. |
| `accumulated` | Tổng tín chỉ đã được công nhận tích lũy đến cuối kỳ, không âm, có thể NULL. Do nguồn cung cấp, không tự cộng mọi passed khi có học lại. Demo giả định passed là tín chỉ mới, không học lại, nên tăng đúng theo số đạt. |
| `conduct` | Điểm rèn luyện 0–100, có thể NULL; dùng được trong cây quy tắc, không thuộc 4 yếu tố mặc định. |
| `status` | `completed`: kết quả học kỳ hoàn thành; `leave`: nghỉ học, yêu cầu registered/passed/failed=0 và GPA học kỳ NULL. Nghỉ học làm đứt chuỗi xu hướng. |

## Tổng hợp học phần nợ

- Số môn nợ = COUNT dòng debts của sinh viên **tại đúng kỳ đang xét**.
- Tín chỉ nợ = SUM(courses.credits) của các dòng đó. Mỗi môn chỉ có một dòng tại một kỳ.
- Snapshot môn nợ không cộng dồn qua nhiều kỳ, tránh một môn nợ bị đếm nhiều lần.
- `failed` là lượng không đạt của **riêng học kỳ**, `debts` là tập các học phần **bắt buộc còn cần hoàn thành** tại thời điểm đó. Không bắt buộc hai tổng bằng nhau: môn nợ cũ có thể còn, môn tự chọn có thể không tiếp tục hoặc đã trả nợ trước thời điểm chốt snapshot. Demo3.1 mang các môn F chưa hoàn thành sang snapshot kỳ tiếp theo và có test đối soát.
- Không có cột `debt` tổng đếm song song như MVP cũ. Bảng điểm demo được đối soát với registered/passed/failed/GPA khi sinh dữ liệu. CSV hiện tại nhập tổng kết học kỳ, chưa có luồng nhập điểm chi tiết từng lần học hoặc tự tính lại tổng kết theo quy chế học lại. Dữ liệu nguồn thực phải được đối soát trước khi nhập.

## Thiếu dữ liệu và tính thời gian

Kỳ hè vẫn có thể lưu kết quả nhưng không dùng làm một mắt xích xu hướng hoặc lịch sử lặp lại. Kỳ chính không có dòng kết quả, có GPA NULL, hoặc nghỉ học làm xu hướng chưa đánh giá được; không nhảy qua kỳ thiếu để ghép ba kỳ bất kỳ. Cảnh báo lặp lại lấy đúng ba kỳ chính ngay trước kỳ đang xét; cần cả ba quyết định true/false. Ba kỳ đầu chưa đủ cửa sổ nên không công bố điểm tổng dù các yếu tố khác đã biết.

Tệp CSV không chứa cột giả `previous_warnings`; lịch sử cảnh báo phải nhập riêng để có nguồn rõ ràng. Kết quả xét quy tắc, điểm nguy cơ và quyết định cảnh báo lịch sử có vai trò khác nhau; không tự đồng nhất chúng.
