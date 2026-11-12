# Kế hoạch học tập dành cho sinh viên — 3.4

Trang `/student/planning` sử dụng GPA, tín chỉ và việc cần làm làm nội dung chính. Các cột điểm đóng góp, điểm hỗ trợ, phiên cấu hình và thời điểm tính không còn hiển thị trên trang kế hoạch. Chức năng phân tích và tính điểm của cố vấn vẫn hoạt động riêng.

## Luồng sử dụng

1. Xem GPA học kỳ, GPA tích lũy và số tín chỉ chưa đạt của học kỳ được chọn làm mốc.
2. Đọc **Bạn nên ưu tiên điều gì?**: gợi ý thay đổi theo điểm hiện có, tín chỉ chưa đạt và xu hướng GPA; có đường dẫn xem bảng điểm hoặc đặt lịch với cố vấn.
3. Nhập mục tiêu GPA, số tín chỉ dự định học và số tín chỉ còn lo chưa đạt. Phần ước tính GPA tích lũy được thu gọn vì không bắt buộc.
4. Chọn **Xem kết quả mục tiêu**: so sánh GPA, giải thích mức điểm trung bình cần đạt ở các môn còn lại và việc nên làm để tiến gần mục tiêu. Không hiển thị bảng điểm đóng góp của thuật toán.
5. Xem học phần nên dành thêm thời gian và ba bước thực hiện theo tuần. Các môn gợi ý lấy từ học phần còn nợ và môn dưới 2.50/4 trong kỳ được chọn; ưu tiên chưa hoàn thành, sau đó số tín chỉ. Đây là dữ liệu đã có, không phải danh sách đăng ký kỳ sau hay cam kết học lại sẽ được thay điểm theo một quy chế cụ thể.

## Cách tính và giới hạn

Nếu GPA mục tiêu là G, đăng ký R tín chỉ và lo không đạt F tín chỉ (điểm 0), số tín chỉ còn lại là P = R − F. Khi P > 0, điểm trung bình cần đạt ở phần còn lại là G × R / P. Ví dụ GPA 3.0, 18 tín chỉ và 3 tín chỉ không đạt: 15 tín chỉ còn lại cần khoảng 3.60/4.

GPA cả kỳ tối đa khi F tín chỉ không đạt là 4 × P / R. Mục tiêu vượt mức này hiển thị cảnh báo, đề nghị giảm số tín chỉ chưa đạt hoặc điều chỉnh GPA; không trình bày GPA tích lũy theo mục tiêu đó như một kết quả có thể đạt. Nếu toàn bộ tín chỉ không đạt, không chia cho 0.

Ước tính GPA tích lũy chỉ xuất hiện khi có GPA tích lũy hiện tại, số tín chỉ đã tính GPA và hai xác nhận về học lại/toàn bộ tín chỉ tính GPA. Không dùng số tín chỉ đã đạt để tự thay thế số tín chỉ tính điểm trung bình. Mục tiêu thấp hơn kỳ làm mốc được ghi rõ là giảm, không được mô tả là tiến bộ.

Những gợi ý học tập là hướng bắt đầu dựa trên dữ liệu hiện có, không bảo đảm kết quả. Việc đăng ký, học lại và tính lại điểm cần đối chiếu quy định của nhà trường với cố vấn. Không ghi kịch bản vào bảng điểm hoặc tạo phiên đánh giá mới khi thử mục tiêu.

## Nhất quán và kiểm tra

API sinh viên trả cùng đoạn HTML Jinja được dùng khi gửi biểu mẫu không có JavaScript. Tên môn và nội dung động được escape. Khi thay đổi dữ liệu hoặc xác nhận, giao diện bỏ kết quả cũ và nhắc tính lại. Nếu dữ liệu thay đổi trong lúc chờ máy chủ, phản hồi cũ không được hiển thị như kết quả mới.

Ngày 09/11/2026: **107 kiểm thử Python và 10 kiểm thử JavaScript đạt**, bao gồm công thức điểm cần đạt, giới hạn khả thi, thiếu GPA, mục tiêu giảm, ưu tiên môn, API/form cùng kết quả, quyền sinh viên và chống hiển thị kết quả cũ. Còn cảnh báo deprecation của Starlette/AnyIO. Server đã khởi động lại ở cổng 8001 với phiên bản 3.4.0.

Chưa xác minh trực quan bố cục mới trên trình duyệt: phiên Chrome của EduAlert đã đóng và browser host không khả dụng tại lần kiểm tra. Kiểm thử tự động không thay thế việc quan sát desktop/mobile.
