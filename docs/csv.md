# CSV: mẫu, kiểm tra và giao dịch

Các mẫu trống tải trong giao diện CSV hoặc `/api/import/template/{kind}` (quản trị viên). Các mẫu có dữ liệu nằm trong `samples/`, chỉ tham chiếu danh mục seed: lớp L1, cố vấn 2, kỳ1–6, học phần HP01.

## Thứ tự nhập

1. Tạo ngành, khóa, lớp, học kỳ, học phần và tài khoản cố vấn ở Quản trị; seed đã có sẵn.
2. `students_valid.csv`: thêm mã giả lập `009001`, giữ số 0 đầu.
3. `results_valid.csv`: 6 kết quả học kỳ, tham chiếu `009001`.
4. `debts_valid.csv`: snapshot môn bắt buộc còn nợ tại kỳ6, không phải tổng môn trượt của mọi kỳ.
5. `warnings_valid.csv`: true/false theo từng kỳ. Phải có các kỳ3/4/5 để F_repeat tại kỳ6 tính được. Không có dòng không đồng nghĩa false.

Sau đủ các mẫu, `009001` có điểm71.5 theo cấu hình mặc định. File lỗi không được nhập nếu muốn giữ demo sạch; chỉ dùng bước preview để trình bày thông báo lỗi.

## Các cột, đúng thứ tự

```csv
id,name,class_id,advisor_id,admission_score,admission_scale,admission_method
student_id,semester_id,gpa,cumulative_gpa,registered,passed,failed,accumulated,conduct,status
student_id,semester_id,course_id
student_id,semester_id,warned
```

Mỗi dòng trên thuộc một loại tệp riêng: students/results/debts/warnings. Cột thừa, thiếu, sai thứ tự bị từ chối; tải mẫu mới nếu không chắc. UTF-8 hoặc UTF-8 BOM, dấu phẩy phân cột, dấu chấm thập phân, chuỗi chứa dấu phẩy phải có dấu nháy CSV. Không đổi mã sinh viên thành dạng khoa học khi dùng Excel. `warned` khuyên dùng `true`/`false`. Ô trống hợp lệ cho GPA, tích lũy/rèn luyện và điểm đầu vào; tín chỉ riêng kỳ bắt buộc. `status`: completed hoặc leave.

## Preview / confirm

- Giới hạn **2 MB và 5.000 dòng**. Server đọc tối đa 2MB+1 để phát hiện vượt ngưỡng.
- Preview kiểm tra schema Pydantic, GPA0–4, rèn luyện0–100, tín chỉ0–60 và tổng đạt+không đạt, điểm xét tuyển trong thang, khóa ngoại, quyết định kỳ và trùng khóa.
- Trùng trong tệp là lỗi (không chọn dòng thắng). Trùng với DB được đếm, hiển thị trước khi xác nhận: **skip** bỏ qua hoặc **update** thay toàn bộ trường từ tệp. Ô trống ở cột nullable khi update sẽ xóa giá trị cũ; không phải patch riêng những ô có dữ liệu.
- Các lỗi có dòng (header là dòng1), cột và hướng sửa. Bảng preview chỉ hiện 10 dòng đầu, số dòng tổng/lỗi là toàn bộ tệp. Tải lỗi qua link thuộc đúng phiên nhập.
- Preview chỉ lưu phiên nhập, **không ghi bảng sinh viên/kết quả/nợ/cảnh báo**. Có một lỗi bất kỳ thì confirm không ghi cả lô.
- Confirm chỉ chủ phiên (admin) được dùng; phiên hết hạn sau1 giờ, đã consumed thì không dùng lại. Server kiểm tra lại toàn bộ dòng với DB mới nhất. Giữ khóa ghi và flush/commit một giao dịch; lỗi/ràng buộc thì rollback.
- Phát hiện tài khoản cố vấn đã bị khóa, tham chiếu bị thay đổi hoặc bản ghi trùng mới phát sinh tại thời điểm confirm. Chế độ skip/update đã chọn vẫn áp dụng rõ ràng cho các khóa mới trùng.
- DB giữ các batch preview phục vụ đối chiếu; chưa có job tự xóa batch cũ. Demo dùng tệp nhỏ, cần bổ sung chính sách lưu trữ cho vận hành lâu dài.

## Khóa trùng

| Tệp | Khóa |
|---|---|
| Sinh viên | id |
| Kết quả | student_id + semester_id |
| Môn nợ | student_id + semester_id + course_id |
| Cảnh báo | student_id + semester_id |

Không có thao tác xóa hàng loạt trong import. Nếu bản snapshot môn nợ cần xóa một môn đã hết nợ trong một kỳ thì chưa có thao tác xóa qua CSV; nhập snapshot cho kỳ mới với các dòng chính xác, hoặc phát triển thêm chức năng sửa snapshot có kiểm toán. Không tự xóa những dòng vắng trong tệp update.

## Xuất dữ liệu

CSV báo cáo có UTF-8 BOM; cùng bộ lọc và quyền như danh sách. Mỗi ô văn bản bắt đầu (kể cả sau khoảng trắng) bằng `=`, `+`, `-`, `@` hoặc ký tự điều khiển phù hợp sẽ được thêm dấu `'` để giảm nguy cơ formula injection. Dùng csv.writer để quote dấu phẩy/nháy/xuống dòng. Không xuất password_hash hoặc session secret. Các dòng lỗi cũng đi qua hàm xuất an toàn.
