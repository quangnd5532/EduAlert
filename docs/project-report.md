# Báo cáo dự án giữa kỳ — EduAlert

## Giới thiệu nhóm 5A

Nguyễn Duy Quang —2351010170; Nguyễn Khánh Hưng —2151010146; Lê Hà Tấn Phong —2451012074. Đây là thông tin giới thiệu, không phải dữ liệu hồ sơ demo. Đề xuất chia việc ở [defense.md](defense.md) không khẳng định thành viên nào đã thực hiện.

## Bài toán và mục tiêu

Cố vấn cần phân biệt một sinh viên đã thỏa điều kiện học vụ với một sinh viên có dấu hiệu sa sút cần trao đổi sớm. Chỉ xem GPA của kỳ cuối có thể bỏ sót diễn biến; chỉ xem một điểm tổng lại thiếu lý do. EduAlert kết hợp rule engine theo cấu hình và chỉ số hỗ trợ giải thích được, trình bày độc lập, nối tới hồ sơ can thiệp.

Mục tiêu: minh bạch các yếu tố, bảo toàn dữ liệu/phiên bản, kiểm tra dữ liệu đầu vào, giới hạn quyền cố vấn, phục vụ một buổi demo có thể tính tay đối chiếu. Không ban hành quyết định cảnh báo chính thức hoặc dự đoán chắc chắn kết quả của sinh viên.

## Phân tích yêu cầu và tác nhân

Admin quản lý danh mục/sinh viên/phân công/tài khoản, nhậpCSV, kích hoạt cấu hình, thống kê toàn hệ thống. Cố vấn chỉ xem sinh viên mình phụ trách, xem giải thích và biểu đồ, mô phỏng, lập kế hoạch, theo dõi và xuất báo cáo trong phạm vi. Sinh viên có tài khoản liên kết với chính hồ sơ, dùng cổng cá nhân6trang và gửi yêu cầu tư vấn. Các vai trò dùng session cookie; phía backend kiểm tra từng tài nguyên và tập truy vấn.

Các ca sử dụng trọng tâm: nhập hồ sơ và kết quả → đánh giá kỳ → giải thích → mô phỏng → can thiệp → theo dõi → báo cáo. Ca ngoại lệ: thiếu dữ liệu, chưa có cấu hình, import trùng/lỗi, ngoài phân công, phiên hết hạn, lịch hẹn quá hạn.

## Thiết kế dữ liệu và ứng dụng

Kiến trúc monolith FastAPI/Jinja2, API cùng origin, SQLAlchemy và SQLite, Alembic migration0001/0002 với schema lịch sử đóng băng. Có18bảng nghiệp vụ/hỗ trợ, gồm thêm liên kết tài khoản sinh viên và điểm học phần. Quan hệ/chi tiết ở [architecture.md](architecture.md) và [data-dictionary.md](data-dictionary.md).

Mã SV là chuỗi; một kết quả/kỳ; thứ tự học kỳ rõ ràng; tuyển sinh có phương thức/thang; không lưu tổng nợ song song danh sách nợ. Tín chỉ đạt+không đạt=đăng ký đã chốt kết quả. GPA tích lũy do nguồn cung cấp; không tự suy quy chế học lại.

Khối quản lý giữ9màn hình chính. Cổng sinh viên3.1 có6trang độc lập, masthead navy, sidebar nhóm chức năng, breadcrumb, bảng điểm và biểu mẫu theo từng trang. Các nhãn trạng thái có chữ, focus bàn phím, CSS responsive/print. Chart.js phục vụ cục bộ; bảng dữ liệu vẫn đọc được khi thiếu đồ thị. Chưa có bằng chứng xác nhận trực quan đầy đủ ở laptop/điện thoại.

## Thuật toán

Rule engine whitelist4 trường và5 toán tử, câyAND/OR, logic3 trạng thái. Không eval. Cấu hình có phạm vi/phiên bản và thứ tự ưu tiên rõ ràng.

Chỉ số S=35Fgpa+25Ffail+25Ftrend+15Frepeat. Từng yếu tố trong0–1, point contribution theo trọng số; thiếu một yếu tố thì không công bố tổng. Xu hướng dùng3 kỳ chính liên tiếp; lặp lại dùng3 kỳ trước có quyết định xác nhận. Giới hạn thời gian đầu vào tránh dùng tương lai. Ví dụ000005:14+20+22.5+15=71.5, nguy cơ cao nhưng không thỏa rule demo. [algorithm.md](algorithm.md) có toàn bộ phép tính.

Mô phỏng sao chép input, thêm kỳ giả định và gọi cùng service; không có lệnh SQL ghi trong endpoint. GPA tích lũy giả định chỉ tính khi có GPA hiện tại, số tín chỉ đã tính GPA do người dùng nhập và xác nhận không học lại/mọi tín chỉ đăng ký tính GPA. Không đủ thì trả NULL. Không có ML hoặc AI sinh dự đoán.

## Chất lượng dữ liệu và bảo mật

CSV hai bước, validation toàn lô, kiểm tra tham chiếu/trùng, explicit skip/update; confirm kiểm tra lại và transaction. CSV có BOM và xử lý ô công thức. Giới hạn2MB/5000dòng, batch1giờ, chỉ chủ phiên xác nhận.

Argon2 băm mật khẩu; session ký,HttpOnly,SameSite,Secure cấu hình; CSRF mọi thao tác ghi. Tài khoản bị khóa mất quyền ngay lần request tiếp theo. Mật khẩu không nằm trong code ứng dụng; seed yêu cầu biến môi trường và demo mode. Audit không ghi bí mật. Đây vẫn là nền tảng demo chưa qua đánh giá bảo mật production.

## Dữ liệu demo

Seed idempotent đã chạy với60sinh viên giả lập,2ngành,4lớp,2khóa,2cố vấn,6kỳ chính và1kỳ hè loại khỏi phân tích;110học phần,2.676kết quả học phần,60tài khoản sinh viên. Các tình huống đại diện được gán mã trong [demo-script.md](demo-script.md). Có snapshot đánh giá qua kỳ, quyết định lịch sửtrue/false, môn nợ, hỗ trợ đã hoàn tất và lịch hẹn quá hạn. Nâng cấp DB demo cũ có backup, không đổi mật khẩu cán bộ hay ghi đè snapshot đánh giá cũ.

## Kiểm thử và kết quả thực tế

Ngày09/11/2026:61pytest và6test JavaScript chạy đạt, compileall vànode --check thành công. Test bao phủ thuật toán, phân quyền, CSV/rollback, cấu hình/snapshot, can thiệp, đối soát dữ liệu,6trang sinh viên, POST không JavaScript và mô phỏng không ghi DB. Server3.1.0 khởi động bằng start.ps1, health/login/assets trả200. Còn1cảnh báo deprecation từ Starlette/AnyIO; chưa xác nhận đầy đủ luồng click/render biểu đồ/layout trong trình duyệt. Xem [testing.md](testing.md) và [release-checks.txt](release-checks.txt).

Không báo cáo accuracy,F1,tỷ lệ phát hiện đúng hoặc hiệu quả hỗ trợ khi không có bộ dữ liệu thật và thiết kế nghiên cứu. Một ví dụ cải thiện sau giai đoạn hỗ trợ trong dữ liệu giả không phải bằng chứng hiệu quả.

## Hạn chế

Chưa có benchmark/tối ưu tập dữ liệu lớn (thống kê có nhiều truy vấn theo sinh viên), khôi phục mật khẩu, nhiều trường, lịch hẹn tái diễn, nguồn dữ liệu trường thật hay bộ máy quy chế học lại/chi tiết từng lần học. Nhập CSV không xóa các dòng môn nợ bị bỏ khỏi tệp. Chưa kiểm tra triển khai HTTPS/máy sạch khác và đầy đủ giao diện qua trình duyệt. Không tự gửi email/SMS.

## Hướng phát triển

Ưu tiên kiểm tra trực quan với người dùng sinh viên/cố vấn và cài đặt trên máy sạch; sau đó tích hợp nguồn học phần và quy chế chính thức có phê duyệt, đánh giá ngưỡng trên dữ liệu có quyền sử dụng, kiểm tra độ lệch nhóm và bổ sung quy trình xử lý cảnh báo/kiểm toán. Chỉ cân nhắc mô hình thống kê/ML khi có dữ liệu, mục tiêu và đánh giá phù hợp.
