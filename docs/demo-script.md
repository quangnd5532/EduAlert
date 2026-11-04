# Kịch bản thuyết trình và demo 7–10 phút

## Chuẩn bị trước buổi thi

Hoàn thành cài phụ thuộc, vendor assets, migration, seed và chạy pytest theo README. Trong môi trường bàn giao các bước runtime còn bị chặn; **không coi kịch bản này là bản ghi một buổi demo đã chạy thành công**. Kiểm tra trước ngày thi theo testing.md, chuẩn bị bản sao DB demo để tránh thay đổi ngoài ý muốn trong lúc trình bày.

Đăng nhập `admin` hoặc `advisor1` bằng mật khẩu đặt ở bước seed. Chọn kỳ ID6 (HK2 2025–2026). Chuẩn bị thư mục samples; bật sẵn server127.0.0.1:8000. Nếu chưa cài được môi trường, trình bày mã và phép tính tay, không nói rằng đã kiểm tra các luồng UI.

## Những mã sinh viên đại diện trong seed

| Tình huống | Mã giả lập | Người xem được | Dữ liệu cần chỉ ra |
|---|---|---|---|
| Học tập ổn định | `000001` | admin, advisor1 | GPA gần nhất3.2→3.3→3.4, không đạt0, không có cảnh báo xác nhận |
| Giảm liên tiếp | `000002` | admin, advisor1 | GPA2.8→2.3→1.9, xu hướng đóng góp22.5 |
| Không đạt cao | `000003` | admin, advisor2 | Kỳ6 GPA1.1,12/20 tín chỉ không đạt, thỏa quy tắc minh họa |
| Cảnh báo lặp lại | `000004` | admin, advisor2 | Các kỳ3/4/5 true; F_repeat=1; kỳ6 GPA1.3 |
| Chưa thỏa rule nhưng nguy cơ cao | `000005` | admin, advisor1 | Kỳ6:71.5 điểm, rule false; ví dụ tính tay trong algorithm.md |
| Cải thiện sau giai đoạn hỗ trợ | `000006` | admin, advisor1 | Hồ sơ gắn kỳ4 GPA1.6; kỳ5 GPA2.3, kỳ6 GPA2.9; không kết luận nhân quả |
| Chưa đủ dữ liệu | `000007` | admin, advisor2 | GPA kỳ5 NULL, không có lịch sử quyết định cảnh báo; không công bố tổng |
| Lịch hẹn quá hạn | `000008` | admin, advisor2 | Hồ sơ Đang hỗ trợ, ngày hẹn bằng ngày seed trừ3 ngày |

Tên mọi hồ sơ bắt đầu “Sinh viên mô phỏng…”. Ngày hẹn phụ thuộc ngày chạy seed lần đầu; seed lại không thay ngày hẹn. Khi xem toàn bộ tình huống, dùng admin để không bị chặn đúng quyền. Với advisor1, truy cập000003 phải trả404.

## Phân bổ thời gian đề xuất

| Thời lượng | Nội dung nói và thao tác |
|---|---|
| 0:00–0:50 | Giới thiệu đề tài và nhóm. “Chúng em tách kết quả xét điều kiện học vụ và điểm ưu tiên hỗ trợ; ngưỡng đang dùng chỉ để minh họa.” Nêu dữ liệu giả lập. |
| 0:50–1:40 | Đăng nhập advisor1 → Dashboard. Chỉ phạm vi30 sinh viên, đủ/thiếu dữ liệu và mẫu số tỷ lệ. Lọc kỳ6/lớpL1; bảng và biểu đồ cập nhật từ DB. |
| 1:40–3:00 | Danh sách tìm000005 → hồ sơ → Giải thích. Chỉ hai vùngA/B. Đọc GPA2.8→2.3→1.9,8/20không đạt, cửa sổ cảnh báo3/4/5. Tính14+20+22.5+15=71.5. Rule hiện tại vẫnfalse. |
| 3:00–4:00 | Tab Nếu…thì…: GPA3, đăng ký20, không đạt0 → điểm giả định15. Chỉ yếu tố xu hướng về0 vì đã tăng. Không ghi đè GPA thật1.9. Có thể bật GPA tích lũy với120tín chỉ tính GPA, xác nhận không học lại/mọi tín chỉ tính GPA: (2.68×120+3×20)/140≈2.7257. Nếu không đủ giả định thì để trống. |
| 4:00–5:10 | Tab Can thiệp, sửa gợi ý, nhập mục tiêu và ngày hẹn → tạo. Chuyển Đang hỗ trợ, thêm ghi chú, lưu và tải lại. Mở trang Can thiệp đổi bảng trạng thái. Hồ sơ gắn evaluation, không chỉ là ghi chú rời. |
| 5:10–5:50 | XuấtCSV từ danh sách cùng bộ lọc; mở báo cáo thống kê/print. Nêu cố vấn không thể xuất ngoài quyền. Thử URL000003 bằngadvisor1 để thấy404. |
| 5:50–7:00 | Chuyểnadmin. CSV: chọn students_errors xem lỗi dòng/cột, chưa lưu; sau đó students_valid preview và confirm. Giải thích skip/update và transaction/revalidation. Có thể chỉ preview để tiết kiệm thời gian. |
| 7:00–8:00 | Cấu hình: tạo nháp thay trọng số hợp lệ tổng100, xem trước số đổi mức/thiếu dữ liệu. Kích hoạt nếu đã chuẩn bị bản sao DB; mở lịch sử000005 để chỉ snapshot cấu hình cũ còn nguyên. |
| 8:00–9:00 | Chỉ kiến trúcrouter/schema/model/service, ERD, test đã thực sự chạy và hạn chế. Nhắc điểm hỗ trợ không phải xác suất; cần quy chế chính thức và dữ liệu có quyền sử dụng trước triển khai thật. |

Có thể bỏ thao tác kích hoạt và GPA tích lũy để rút xuống7phút. Dành phút cuối trả lời câu hỏi. Không đọc toàn bộ mã nguồn trên màn hình; chỉ mở `assessment.py` và test tính tay khi giảng viên hỏi cách kiểm chứng.

## Những câu nên nói chính xác

- “Không có dòng lịch sử cảnh báo là chưa biết; false mới là đã xác nhận không cảnh báo.”
- “Ba kỳ chính liên tiếp theo thứ tự, không ghép bỏ qua kỳ thiếu.”
- “Điểm tổng chỉ xuất hiện khi tính được cả bốn yếu tố.”
- “Mô phỏng dùng cùng service; không có thao tác ghi kết quả học tập.”
- “Sinh viên cải thiện sau hỗ trợ trong dữ liệu minh họa; ứng dụng không chứng minh hỗ trợ là nguyên nhân duy nhất.”
- “Báo cáo kiểm thử phân biệt test đã đạt và test chưa chạy vì giới hạn môi trường.”
