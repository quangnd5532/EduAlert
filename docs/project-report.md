# Báo cáo dự án giữa kỳ — EduAlert

## Giới thiệu nhóm 5A

Nguyễn Duy Quang —2351010170; Nguyễn Khánh Hưng —2151010146; Lê Hà Tấn Phong —2451012074. Đây là thông tin giới thiệu, không phải dữ liệu hồ sơ demo. Đề xuất chia việc ở [defense.md](defense.md) không khẳng định thành viên nào đã thực hiện.

## Bài toán và mục tiêu

Cố vấn cần phân biệt một sinh viên đã thỏa điều kiện học vụ với một sinh viên có dấu hiệu sa sút cần trao đổi sớm. Chỉ xem GPA của kỳ cuối có thể bỏ sót diễn biến; chỉ xem một điểm tổng lại thiếu lý do. EduAlert kết hợp rule engine theo cấu hình và chỉ số hỗ trợ giải thích được, trình bày độc lập, nối tới hồ sơ can thiệp.

Mục tiêu: minh bạch các yếu tố, bảo toàn dữ liệu/phiên bản, kiểm tra dữ liệu đầu vào, giới hạn quyền cố vấn, phục vụ một buổi demo có thể tính tay đối chiếu. Không ban hành quyết định cảnh báo chính thức hoặc dự đoán chắc chắn kết quả của sinh viên.

## Phân tích yêu cầu và tác nhân

Admin quản lý danh mục/sinh viên/phân công/tài khoản, nhậpCSV, kích hoạt cấu hình, thống kê toàn hệ thống. Cố vấn chỉ xem sinh viên mình phụ trách, xem giải thích và biểu đồ, mô phỏng, lập kế hoạch, theo dõi và xuất báo cáo trong phạm vi. Cả hai dùng chung session cookie; phía backend kiểm tra từng tài nguyên và tập truy vấn.

Các ca sử dụng trọng tâm: nhập hồ sơ và kết quả → đánh giá kỳ → giải thích → mô phỏng → can thiệp → theo dõi → báo cáo. Ca ngoại lệ: thiếu dữ liệu, chưa có cấu hình, import trùng/lỗi, ngoài phân công, phiên hết hạn, lịch hẹn quá hạn.

## Thiết kế dữ liệu và ứng dụng

Kiến trúc monolith FastAPI/Jinja2, API cùng origin, SQLAlchemy và SQLite, Alembic migration đóng băng schema v1. Có16 bảng nghiệp vụ/hỗ trợ (gồm danh mục, hồ sơ, kết quả, phiên bản, can thiệp và audit/import). Quan hệ/chi tiết ở [architecture.md](architecture.md) và [data-dictionary.md](data-dictionary.md).

Mã SV là chuỗi; một kết quả/kỳ; thứ tự học kỳ rõ ràng; tuyển sinh có phương thức/thang; không lưu tổng nợ song song danh sách nợ. Tín chỉ đạt+không đạt=đăng ký đã chốt kết quả. GPA tích lũy do nguồn cung cấp; không tự suy quy chế học lại.

Giao diện có9 màn hình chính. Sidebar/topbar nhất quán, bố cục nền sáng xanh ngọc, bảng chữ số tabular, nhãn màu có chữ, tab hỗ trợ bàn phím, layout responsive và CSS print. Chart.js cục bộ sau bước cài và bảng dữ liệu luôn có để đọc khi thiếu đồ thị. Chưa có bằng chứng render UI trong môi trường bàn giao.

## Thuật toán

Rule engine whitelist4 trường và5 toán tử, câyAND/OR, logic3 trạng thái. Không eval. Cấu hình có phạm vi/phiên bản và thứ tự ưu tiên rõ ràng.

Chỉ số S=35Fgpa+25Ffail+25Ftrend+15Frepeat. Từng yếu tố trong0–1, point contribution theo trọng số; thiếu một yếu tố thì không công bố tổng. Xu hướng dùng3 kỳ chính liên tiếp; lặp lại dùng3 kỳ trước có quyết định xác nhận. Giới hạn thời gian đầu vào tránh dùng tương lai. Ví dụ000005:14+20+22.5+15=71.5, nguy cơ cao nhưng không thỏa rule demo. [algorithm.md](algorithm.md) có toàn bộ phép tính.

Mô phỏng sao chép input, thêm kỳ giả định và gọi cùng service; không có lệnh SQL ghi trong endpoint. GPA tích lũy giả định chỉ tính khi có GPA hiện tại, số tín chỉ đã tính GPA do người dùng nhập và xác nhận không học lại/mọi tín chỉ đăng ký tính GPA. Không đủ thì trả NULL. Không có ML hoặc AI sinh dự đoán.

## Chất lượng dữ liệu và bảo mật

CSV hai bước, validation toàn lô, kiểm tra tham chiếu/trùng, explicit skip/update; confirm kiểm tra lại và transaction. CSV có BOM và xử lý ô công thức. Giới hạn2MB/5000dòng, batch1giờ, chỉ chủ phiên xác nhận.

Argon2 băm mật khẩu; session ký,HttpOnly,SameSite,Secure cấu hình; CSRF mọi thao tác ghi. Tài khoản bị khóa mất quyền ngay lần request tiếp theo. Mật khẩu không nằm trong code ứng dụng; seed yêu cầu biến môi trường và demo mode. Audit không ghi bí mật. Đây vẫn là nền tảng demo chưa qua đánh giá bảo mật production.

## Dữ liệu demo

Seed idempotent chuẩn bị60 sinh viên giả lập,2ngành,4lớp,2khóa,2cố vấn,6kỳ chính và1kỳ hè loại khỏi phân tích. Các tình huống đại diện được gán mã trong [demo-script.md](demo-script.md). Có snapshot đánh giá qua kỳ, quyết định lịch sửtrue/false, môn nợ, hỗ trợ đã hoàn tất và lịch hẹn quá hạn. Seed chưa chạy được trong môi trường này; các con số mô tả **nội dung seed đã viết**.

## Kiểm thử và kết quả thực tế

34 test Python thuần và6 test JavaScript đã chạy đạt; compileall vànode --check không báo lỗi cú pháp. Đã viết14 test pytest về tích hợp/phân quyền/CSV/phiên bản/can thiệp/nhất quán bộ lọc; **chưa chạy** vì thiếu thư viện, không truy cập được PyPI. Chưa tải Chart.js/Swagger UI, chưa chạy migration/seed/server hay browser flow. Xem [testing.md](testing.md) để phân biệt phần đã kiểm và checklist còn lại.

Không báo cáo accuracy,F1,tỷ lệ phát hiện đúng hoặc hiệu quả hỗ trợ khi không có bộ dữ liệu thật và thiết kế nghiên cứu. Một ví dụ cải thiện sau giai đoạn hỗ trợ trong dữ liệu giả không phải bằng chứng hiệu quả.

## Hạn chế

Chưa nghiệm thu runtime do môi trường; chưa có benchmark/tối ưu tập dữ liệu lớn (thống kê có nhiều truy vấn theo sinh viên), khôi phục mật khẩu, nhiều trường, lưu lịch hẹn tái diễn, dashboard theo nguồn dữ liệu thực, bộ máy quy chế học lại và chi tiết từng lần học. Nhập CSV không xóa các dòng môn nợ bị bỏ khỏi tệp. Swagger được cấu hình local nhưng cần cài assets như Chart.js. Không tự gửi email/SMS.

## Hướng phát triển

Ưu tiên chạy toàn bộ integration và kiểm traUI trên Python3.12/3.13 sau khi có phụ thuộc; đóng gói bộ môi trường offline kèmChart.js đã xác minh. Sau đó thêm nguồn học phần chi tiết và quy chế chính thức có phê duyệt; đánh giá ngưỡng trên dữ liệu có quyền sử dụng, kiểm tra độ lệch nhóm; bổ sung quy trình xử lý cảnh báo và kiểm toán đầy đủ. Chỉ cân nhắc mô hình thống kê/ML khi có dữ liệu, mục tiêu và đánh giá phù hợp.
