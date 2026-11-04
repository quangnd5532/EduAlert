# Câu hỏi giảng viên và đề xuất phân công

## Câu hỏi dự kiến

**1. Vì sao cần hai kết quả đánh giá?**  
Rule trả lời sinh viên có thỏa bộ điều kiện hiện hành không. Điểm sớm giúp ưu tiên trao đổi trước khi chạm ngưỡng đó. `000005` có 71.5 điểm nhưng không thỏa rule demo. Giao diện có hai vùng A/B; API và CSV cũng có hai trường kết quả riêng.

**2. Bộ ngưỡng này có đúng quy chế trường không?**  
Chưa có quy chế được cung cấp. Tên mặc định và giao diện ghi “Bộ quy tắc minh họa phục vụ demo”. Khi có quy chế cần đối chiếu, kiểm tra và tạo phiên bản được phê duyệt. Không mô tả các mốc 1.2/1.8/50% là quy định chính thức.

**3. Điểm 71.5 có nghĩa 71.5% trượt không?**  
Không. Đó là tổng đóng góp của bốn yếu tố, dùng ưu tiên hỗ trợ. Chưa huấn luyện hoặc hiệu chỉnh với nhãn kết quả nên không có xác suất hay số đo accuracy.

**4. Thiếu dữ liệu xử lý thế nào?**  
Không thay NULL bằng 0. Mỗi yếu tố có value/contribution nullable, lý do và danh sách kỳ. Đủ bốn yếu tố mới công bố tổng và phân loại; thiếu dữ liệu có nhóm riêng trong thống kê. Cảnh báo lịch sử false khác với không có dòng.

**5. Vì sao ba kỳ đầu có thể chưa đủ điểm?**  
F_repeat cần ba kỳ chính ngay trước kỳ xét với quyết định đã xác nhận. Ở ba kỳ đầu, cửa sổ này chưa đủ. Người dùng vẫn xem được GPA, điều kiện học vụ và các yếu tố đã tính.

**6. Có lấy dữ liệu tương lai để tính lịch sử không?**  
Service lọc học kỳ/kết quả có sequence ≤ kỳ xét và warning có sequence < kỳ xét. Snapshot cũng chỉ chứa phần đó. Test `test_no_future_leak` thay dữ liệu tương lai rồi kiểm tra kết quả kỳ cũ không đổi.

**7. Kỳ hè, nghỉ học và thiếu kỳ xử lý thế nào?**  
Kỳ hè không nằm trong chuỗi phân tích chính. Kỳ chính chưa hoàn thành, nghỉ học hoặc không có kết quả/GPA làm xu hướng thiếu; không bỏ qua để lấy kỳ xa hơn. `sequence` quy định thứ tự thay vì chuỗi tên kỳ.

**8. Vì sao không dùng điểm tuyển sinh hoặc rèn luyện trong điểm sớm?**  
Công thức mặc định có đúng bốn yếu tố theo yêu cầu. Tuyển sinh có nhiều phương thức và thang nên chỉ lưu kèm, không so sánh trực tiếp. Rèn luyện có thể dùng trong rule whitelist, không thuộc chỉ số sớm mặc định.

**9. Rule engine có chạy code do người dùng nhập không?**  
Không dùng eval. `validate_rule` cho phép bốn trường, năm toán tử và AND/OR, giới hạn độ sâu/số nhánh. `rule_result` ánh xạ toán tử có sẵn qua module operator và dùng logic ba trạng thái.

**10. Nếu ngành và khóa đều có cấu hình thì chọn thế nào?**  
Ưu tiên ngành + khóa, sau đó ngành, khóa, toàn cục. Kích hoạt bản mới tắt bản cùng phạm vi trong một transaction có khóa ghi SQLite. Payload không sửa trực tiếp; muốn đổi phải tạo nháp mới.

**11. Đổi cấu hình có mất lịch sử không?**  
Không. Evaluation lưu config_id, input_data, output và created_at. Nháp/preview không ghi đánh giá. Biểu đồ hiện tại ghi nhãn tính theo cấu hình đang áp dụng; snapshot cũ xem riêng ở tab Giải thích.

**12. Mô phỏng khác đánh giá thật ở đâu?**  
Cùng service `evaluate`. `simulate` sao chép input, thêm kỳ giả định rồi tính. Endpoint không ghi AcademicResult/Evaluation. Test tích hợp đã viết kiểm số bản ghi không đổi; tình trạng đã chạy hay chưa xem testing.md.

**13. GPA tích lũy giả định tính ra sao?**  
Chỉ khi có GPA tích lũy hiện tại, số tín chỉ đã tính GPA do người dùng cung cấp và xác nhận không học lại/toàn bộ đăng ký tính GPA. Công thức trung bình có trọng số được hiển thị. Không dùng tín chỉ đã đạt thay mẫu số GPA vì môn không đạt/học lại có thể có quy chế khác. Thiếu điều kiện thì trả NULL và lý do.

**14. Làm sao biết cố vấn không đọc được hồ sơ khác?**  
Mỗi request kiểm tra người dùng còn hoạt động. `student_access` đối chiếu advisor_id; ngoài quyền trả 404. Truy vấn danh sách, thống kê và xuất CSV bắt đầu bằng `scoped_students`. Các thao tác can thiệp kiểm tra sinh viên trước khi đọc/sửa, không tin owner do client gửi.

**15. Vì sao vừa ẩn menu vừa kiểm tra backend?**  
Ẩn menu giúp dễ dùng. Kiểm tra backend mới bảo vệ khi gọi URL/API trực tiếp. Test gồm đọc trang, API, simulate, evaluate, update và CSV ngoài quyền.

**16. Mật khẩu, session và CSRF được bảo vệ thế nào?**  
Argon2 hash, không lưu plaintext. Session ký; cookie HttpOnly/SameSite, Secure khi HTTPS. Secret lấy từ môi trường hoặc sinh local. Mọi POST/PUT/PATCH/DELETE so CSRF token, kể cả login/logout. Bản demo chưa qua đánh giá bảo mật production.

**17. CSV có một dòng sai sau nhiều dòng đúng thì sao?**  
Preview và confirm đều kiểm toàn bộ. Có lỗi thì không ghi lô. Confirm kiểm tra lại DB trong transaction; flush/commit thất bại thì rollback. Preview chỉ lưu ImportBatch, không ghi dữ liệu nghiệp vụ.

**18. CSV trùng có bị âm thầm ghi đè không?**  
Trùng trong tệp là lỗi. Trùng DB được đếm và chọn skip/update trước preview; UI hiển thị lại chế độ. Update thay toàn bộ trường từ dòng, ô trống nullable cũng xóa giá trị cũ. Confirm kiểm tra lại để xử lý dữ liệu đổi sau preview.

**19. Tín chỉ nợ và không đạt có giống nhau không?**  
Không đạt là tín chỉ riêng kỳ để tính F_fail. Nợ là snapshot các học phần bắt buộc còn phải hoàn thành đến kỳ đó, có thể gồm nợ cũ. Không cộng lặp snapshot nhiều kỳ. Tín chỉ nợ tính từ courses/­debts, không có cột tổng thứ hai.

**20. Biểu đồ, danh sách và CSV có cùng tập dữ liệu không?**  
Chúng gọi chung `filtered`, gồm phạm vi người dùng và bộ lọc. Pagination chỉ cắt danh sách; export lấy toàn tập. Trend áp bộ lọc riêng mỗi kỳ, không khẳng định đó là một đoàn hệ cố định. Suite tích hợp có test đối chiếu số lượng nhưng phải ghi nhận kết quả chạy thật.

**21. Có chứng minh can thiệp giúp GPA tăng không?**  
Không có thiết kế đánh giá nhân quả. UI chỉ so GPA kỳ gắn hồ sơ với kỳ chính hoàn thành tiếp theo, ghi rõ không kết luận can thiệp là nguyên nhân duy nhất. Dữ liệu hoàn toàn giả lập.

**22. Đã kiểm thử những gì?**  
34 test Python không cần phụ thuộc ngoài và 6 test JavaScript đã chạy đạt; đã kiểm cú pháp Python/JavaScript. API/DB, migration/seed và browser flow chưa chạy được vì mạng/phụ thuộc bị chặn. Xem testing.md để dùng số liệu cập nhật; không nói “mọi test đều pass” khi suite tích hợp chưa chạy.

**23. Vì sao chọn SQLite và monolith?**  
Phù hợp demo 60 sinh viên, ít vai trò, khởi chạy đơn giản và dễ giải thích. SQLAlchemy/Alembic giữ cấu trúc để có thể chuyển DB sau. Chưa tối ưu N+1 query hay benchmark dữ liệu lớn, không khẳng định khả năng chịu tải production.

**24. Các nút có thực hiện nghiệp vụ thật không?**  
Các nút nghiệp vụ gọi API hoặc form server có lưu DB, nhưng runtime chưa được nghiệm thu trong môi trường này. Biểu đồ cần cài vendor assets; thiếu thư viện thì UI thông báo và hiện bảng thay thế. Không có nút email/SMS vì chưa triển khai chức năng đó.

## Đề xuất phân công cho ba thành viên

**Đây là gợi ý tổ chức công việc tiếp theo, không phải khẳng định lịch sử đóng góp.** Nhóm tự thống nhất và ghi nhật ký thực tế khi thực hiện.

| Thành viên | Đề xuất phụ trách | Phần trình bày đề xuất |
|---|---|---|
| Nguyễn Duy Quang | FastAPI/DB/migration, session/CSRF/phân quyền, khởi chạy demo | Kiến trúc, dữ liệu, tài khoản và phạm vi |
| Nguyễn Khánh Hưng | Service đánh giá, rule/config version, mô phỏng, tính tay và unit tests | Hai kết quả độc lập, ví dụ 71.5 |
| Lê Hà Tấn Phong | Giao diện, Chart.js, CSV, can thiệp/báo cáo, kiểm tra responsive | Luồng hỗ trợ, nhập CSV, báo cáo và trải nghiệm |

Cả ba cùng chạy kiểm thử tích hợp và checklist demo, đọc chéo phần của nhau để trả lời đúng mã nguồn. Ghi kết quả kiểm thử thật sau khi hoàn thiện môi trường; không gán công việc đã làm cho người nào chỉ vì bảng đề xuất này.
