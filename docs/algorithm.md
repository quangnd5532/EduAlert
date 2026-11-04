# Công thức và quy tắc đánh giá

Mã nguồn chính: `app/services/assessment.py`. Tính toán thuần Python, có thể kiểm thử không cần FastAPI/DB. Đây là **chỉ số ưu tiên hỗ trợ**, không phải xác suất trượt/bỏ học. “Bộ quy tắc minh họa phục vụ demo” không đại diện quy chế trường.

## A. Xét điều kiện học vụ

Cấu hình mặc định:

```text
GPA học kỳ < 1.2 OR GPA tích lũy < 1.8 OR tỷ lệ không đạt ≥ 0.5
```

Trường cho phép: `gpa`, `cumulative_gpa` trong 0–4; `failed_ratio` trong 0–1; `conduct` trong 0–100. Toán tử: lt (<), le (≤), gt (>), ge (≥), eq (=). Nhóm AND/OR lồng tối đa 6 cấp, 1–20 con mỗi nhóm. Không dùng eval, SQL động theo chuỗi biểu thức, hoặc thực thi code do người dùng nhập.

Mỗi lá trả true/false/unknown, giá trị thực tế, ngưỡng và lý do. OR: một nhánh true đủ true; nếu không có true nhưng có unknown thì unknown. AND: một nhánh false đủ false; nếu không có false nhưng có unknown thì unknown. Vì vậy thiếu GPA không tự thành không cảnh báo. Nhánh có dữ liệu đủ kết luận vẫn được giải thích minh bạch.

Không có cấu hình áp dụng: nhãn “Chưa có cấu hình áp dụng”, không cho kết quả bình thường.

## B. Điểm cảnh báo sớm

```text
S = 35 × F_gpa + 25 × F_fail + 25 × F_trend + 15 × F_repeat
clamp(x) = max(0, min(1, x))

F_gpa   = clamp((2.5 − GPA kỳ) / 1.5)
F_fail  = clamp((failed / registered) / 0.5)
F_trend = clamp((GPA đầu − GPA cuối) / 1.0)
          chỉ khi cả hai chuyển tiếp trong 3 kỳ đều giảm nghiêm ngặt;
          đủ 3 GPA nhưng không giảm cả hai lần => 0.
F_repeat = min(số kỳ có cảnh báo trong ba kỳ trước / 2, 1)
```

Không có giả định `NULL=0`. Đăng ký bằng 0 khiến F_fail thiếu, không chia cho 0. F_repeat cần ba dòng quyết định lịch sử, false là xác nhận không cảnh báo; dòng vắng là chưa biết. Cả bốn yếu tố đủ mới công bố S và phân loại. Yếu tố thiếu được trả contribution=NULL và reason yêu cầu bổ sung; các yếu tố tính được vẫn hiển thị.

Điểm tổng và đóng góp được làm tròn 4 số thập phân để công bố; phân loại dựa trên điểm tổng này. UI thường hiển thị 1–2 số. Phân loại: [0,30) Bình thường; [30,60) Cần chú ý; [60,100] Nguy cơ cao. Kiểm thử trực tiếp ranh giới có trong test_assessment.py. Trọng số không âm có tổng **đúng 100**; mốc attention phải >0 và < high ≤100; các mẫu số phải dương, hữu hạn. Tham số JSON chỉ nhận đúng khóa mẫu, tránh lỗi đánh máy bị bỏ qua.

## Cửa sổ thời gian

1. Chọn kỳ chính regular đã hoàn thành để xét.
2. Sắp theo `semesters.sequence`, không sắp tên kỳ hoặc mã SV.
3. Xu hướng: ba **vị trí kỳ chính liên tiếp** kết thúc ở kỳ đang xét, đều có kết quả completed và GPA. Không bỏ qua kỳ nghỉ/thiếu kết quả. Kỳ hè không chiếm vị trí chuỗi.
4. Lặp lại: ba vị trí kỳ chính ngay **trước** kỳ xét; không tính kỳ xét, không tính cảnh báo xa hơn hoặc tương lai. Đây là cửa sổ theo lịch học kỳ; một kỳ nghỉ vẫn cần xác nhận quyết định cảnh báo/không cảnh báo nếu muốn tính yếu tố lặp lại.
5. Snapshot đánh giá chỉ chứa học kỳ/kết quả đến kỳ xét và quyết định trước kỳ xét. Không dùng kỳ tương lai.

Ba kỳ đầu chưa đủ 3 kỳ trước để tính F_repeat; hiển thị chưa đủ dữ liệu là có chủ ý, không phải lỗi seed. Dữ liệu chính có sáu kỳ từ HK1 2023–2024 đến HK2 2025–2026; tất cả đều trước thời điểm tạo demo tháng 11/2026. Một kỳ hè riêng được đánh dấu loại summer.

## Ví dụ tính tay có thể kiểm tra

Sinh viên giả lập `000005`, xét kỳ ID 6. Ba GPA gần nhất:

| Kỳ | ID / sequence | GPA |
|---|---|---|
| HK2 2024–2025 | 4 | 2.8 |
| HK1 2025–2026 | 5 | 2.3 |
| HK2 2025–2026 | 6 | 1.9 |

Đăng ký 20, đạt 12, không đạt 8; GPA tích lũy = (3+3.1+3+2.8+2.3+1.9)/6 = **2.68** làm tròn trong seed. Các kỳ trước 3,4,5 đều có quyết định cảnh báo giả lập. Các quyết định lịch sử được cung cấp độc lập, không sinh từ bộ ngưỡng minh họa hiện tại.

| Yếu tố | Phép tính | F | Đóng góp |
|---|---|---|---|
| GPA | (2.5−1.9)/1.5 | 0.4 | 14 |
| Không đạt | (8/20)/0.5 | 0.8 | 20 |
| Xu hướng | 2.8>2.3>1.9; (2.8−1.9)/1 | 0.9 | 22.5 |
| Lặp lại | min(3/2,1) | 1 | 15 |
| **Tổng** | **14+20+22.5+15** | | **71.5 — Nguy cơ cao** |

Trong khi đó GPA kỳ 1.9 không <1.2, tích lũy 2.68 không <1.8, không đạt 0.4 không ≥0.5: **không thỏa điều kiện cảnh báo minh họa**. Đây là ví dụ chứng minh vì sao phải tách hai vùng kết quả.

Test thuần Python dùng cùng GPA gần nhất, tỷ lệ không đạt và cảnh báo; cumulative_gpa=2.4 (vẫn vượt 1.8) để tính tay không phụ thuộc cách tạo toàn bộ seed. Cả test và demo cho cùng S=71.5. Bộ mẫu CSV `009001` cũng cho 71.5 nếu nhập đủ mẫu sinh viên, kết quả và quyết định lịch sử.

## Mô phỏng

`simulate()` sao chép các đầu vào, bỏ kết quả sau kỳ xét, thêm một kỳ chính giả định ở ngay sau dữ liệu lịch sử được giữ. Kỳ giả định có GPA, đăng ký và không đạt do người dùng nhập; passed=registered−failed. Gọi lại đúng `evaluate()`, cùng payload cấu hình đang áp dụng. Quyết định cảnh báo của kỳ gốc phải có nếu muốn tính F_repeat cho kỳ giả định.

Với `000005`, kịch bản GPA=3, đăng ký=20, không đạt=0 ở kỳ tiếp theo: F_gpa=0, F_fail=0, xu hướng 2.3→1.9→3 không giảm liên tiếp nên 0, lặp lại các kỳ4/5/6 có 2 cảnh báo nên 1. Tổng mới=15. Không ghi kết quả vào DB.

GPA tích lũy giả định chỉ tính nếu có GPA tích lũy hiện tại, `previous_gpa_credits` do người dùng cung cấp, `no_repeats=true` và `all_registered_count=true`. Công thức `(GPA tích lũy hiện tại × tín chỉ đã tính GPA + GPA kỳ giả định × đăng ký) / (tín chỉ đã tính GPA + đăng ký)`. Giả định không học lại và mọi tín chỉ đăng ký (kể cả môn không đạt) đều tính GPA. Thiếu một điều kiện thì trả NULL và giải thích. Không dùng `accumulated` thay mẫu số GPA một cách tùy tiện. Ví dụ GPA tích lũy2.68,120tín chỉ tính GPA và kỳ mới3×20: kết quả2.7257. Số tín chỉ do người dùng nhập là giả định cần đối chiếu bảng điểm, không được tự xác nhận là dữ liệu đã kiểm chứng.

## Phiên bản và giới hạn

- Chọn cấu hình: ngành+khóa > ngành > khóa > toàn cục; chỉ một bản active cho mỗi phạm vi qua API kích hoạt tuần tự hóa.
- Mỗi lần lưu đánh giá ghi ID cấu hình, snapshot input và output. Dữ liệu/cấu hình không đổi thì tái sử dụng bản đánh giá gần nhất tương đương; không tăng vô ích bản ghi.
- Xem trước cấu hình tính ảnh hưởng ở kỳ chính mới nhất trên toàn bộ dữ liệu trong phạm vi admin, có xét ưu tiên các cấu hình khác; không lưu kết quả preview.
- Biểu đồ và thống kê tính theo cấu hình hiện hành để so sánh nhất quán, được ghi nhãn. Lịch sử đã lưu xem riêng và không ghi đè.
- Chưa kiểm định ngưỡng trên dữ liệu thật, chưa có phân tích độ công bằng, độ nhạy hay hiệu chỉnh chuyên ngành. Không dùng điểm tuyển sinh để tránh so sánh thang điểm không tương thích.
- Diễn biến sau hỗ trợ chỉ là mô tả, không chứng minh quan hệ nhân quả.
