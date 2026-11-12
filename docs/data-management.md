# Dữ liệu, sắp xếp và cấu hình 3.3

## Hồ sơ sinh viên

60 hồ sơ gồm 22 sinh viên khóa 23, 18 sinh viên khóa 24, 20 sinh viên khóa 25. Mã có 10 chữ số, bắt đầu bằng năm tuyển sinh, ví dụ `2351000005`. Có 6 lớp thuộc CNTT và QTKD. Các chuỗi GPA được tạo riêng theo từng sinh viên, có học tốt, sa sút, tiến bộ và dao động; bảng điểm học phần đối soát với GPA và tín chỉ tổng hợp.

Khóa 23 có 6 kỳ, khóa 24 có 4 kỳ, khóa 25 có 2 kỳ đã hoàn thành. Học kỳ trước khi nhập học không nằm trong yêu cầu dữ liệu của sinh viên. Các quy tắc cần 3 kỳ để nhận xét xu hướng hoặc 3 kỳ trước đó để nhận xét cảnh báo lặp lại vẫn giữ đúng cửa sổ: khóa 25 được ghi là cần thêm thời gian theo dõi, không được tự điền điểm hoặc quyết định cảnh báo giả để tạo đủ chỉ số.

Hồ sơ có thông tin chưa đồng bộ được giữ làm trường hợp kiểm tra thiếu dữ liệu. Lý do nêu rõ học kỳ và cách xử lý, tách khỏi trường hợp chưa đủ thời gian theo học. Điểm hỗ trợ và điều kiện học vụ là hai kết quả độc lập.

## Sắp xếp và bộ lọc

17 lựa chọn: điểm hỗ trợ, GPA học kỳ, GPA tích lũy, tín chỉ không đạt, tín chỉ tích lũy, họ tên, mã sinh viên (hai chiều); lớp, khóa, và hồ sơ cần bổ sung trước. Giá trị chưa có luôn xếp sau giá trị đã có khi sắp theo số; mã sinh viên là khóa phụ ổn định. Hỗ trợ 12/24/60 dòng mỗi trang, lọc theo cố vấn và tình trạng dữ liệu.

Danh sách, tổng quan và tệp xuất dùng chung bộ lọc/sắp xếp. Tổng quan hiển thị tối đa 12 sinh viên đầu; tệp CSV xuất toàn bộ tập lọc theo cùng thứ tự. Tệp xuất có thêm GPA, tín chỉ, lý do và thông tin cần bổ sung.

## Bốn mẫu nhập CSV

- Hồ sơ sinh viên: 6 sinh viên mẫu, mã theo khóa và lớp/cố vấn tương ứng.
- Kết quả học kỳ: 24 dòng, không có kết quả trước năm nhập học; GPA tích lũy có đối soát theo tín chỉ.
- Học phần còn nợ: danh sách còn nợ theo kỳ, khớp tín chỉ tích lũy và học phần có trong danh mục.
- Lịch sử cảnh báo: 24 quyết định có/không cảnh báo cho các kỳ đã theo học.

Tải bản có dữ liệu hoặc bản trống trực tiếp trên trang Nhập CSV. Có hướng dẫn từng cột và tra mã lớp/cố vấn/học kỳ/học phần. Nhập hồ sơ trước rồi nhập các tệp liên quan. Giữ định dạng văn bản cho mã sinh viên; dùng UTF-8/BOM, dấu phẩy hoặc chấm phẩy. Có thể đổi thứ tự cột nhưng không được thiếu, trùng hoặc thêm cột ngoài mẫu. Xem trước chỉ ghi phiên nhập; dữ liệu nghiệp vụ được lưu sau xác nhận và kiểm tra lại. Chế độ bỏ qua giữ nguyên dữ liệu cũ; chế độ cập nhật thay toàn bộ trường của bản ghi.

Tệp trong `samples/` và tệp tải qua API dùng chung bộ tạo dữ liệu. Chạy `python scripts/create_samples.py` để tạo lại. Hồ sơ CSV không tự tạo mật khẩu hoặc thay đổi tài khoản truy cập.

## Cấu hình đánh giá

Biểu mẫu có trọng số bốn yếu tố, ngưỡng phân loại, mốc GPA/tín chỉ/xu hướng/cảnh báo và trình tạo điều kiện học vụ theo nhóm “ít nhất một” hoặc “tất cả”. Tỷ lệ hiển thị phần trăm và chuyển về tỷ lệ 0–1 ở máy chủ. Kiểm tra tổng trọng số 100, ngưỡng hợp lệ, mốc tính dương và điều kiện được phép.

Có 4 mẫu tham khảo. Bộ chung đang áp dụng; 3 bộ theo khóa 23/24/25 ở trạng thái nháp để người quản trị xem xét, không tự thay quy chế đang có. Chỉ bản nháp chưa từng áp dụng được sửa; có thể sao chép bộ đã áp dụng để tạo phiên bản mới. Xem trước cho học kỳ chọn hiển thị số sinh viên chịu tác động, đổi điểm/mức/kết luận học vụ, phân bố trước–sau và các hồ sơ thay đổi. Áp dụng qua nút có tên phiên bản sau khi xem trước. Các phiên đánh giá đã lưu không bị ghi đè.

## Nâng cấp dữ liệu hiện có

`python -m app.upgrade_demo` chỉ xử lý DB có dấu seed demo và migration `0003`. Công cụ tạo bản sao lưu SQLite trước khi thay đổi, chỉ nhận diện hồ sơ seed còn nguyên tên, kiểm tra xung đột mã đích, cập nhật mọi khóa ngoại trong một giao dịch và kiểm tra toàn vẹn trước khi lưu. Bảo toàn ID tài khoản, password hash, thông tin khôi phục và snapshot đánh giá. Tên đăng nhập `student` giữ nguyên; các tài khoản `sv000…` chuyển theo mã mới. Sinh viên đăng nhập bằng mã mới; liên kết bookmark chứa mã cũ cần cập nhật. Chạy lại không ghi đè những chỉnh sửa sau nâng cấp.

## Kiểm tra

Ngày 09/11/2026: toàn bộ 97 kiểm thử Python và 8 kiểm thử JavaScript đạt. Bao phủ phân quyền, khôi phục mật khẩu, dữ liệu theo khóa, đối soát bảng điểm, 17 kiểu sắp xếp, nhập đủ 4 tệp mẫu, thiếu dữ liệu/lịch sử, sửa bản nháp và xem trước/kích hoạt. Còn cảnh báo deprecation từ Starlette/AnyIO. Server 3.3 chạy tại cổng 8001; health và các tài nguyên mới trả HTTP 200.

Không nhận được screenshot đính kèm trong phiên yêu cầu. Browser host ban đầu không khả dụng. Sau đó đã đọc được nội dung trang Kế hoạch học tập trên Chrome bằng accessibility: kịch bản GPA 3, 18 tín chỉ, 3 không đạt, 76 tín chỉ GPA cho kết quả 23.33 điểm và GPA tích lũy 2.74. API chụp ảnh cửa sổ lại trả ảnh VS Code thay vì Chrome nên chưa có xác minh bố cục trực quan desktop/mobile. Các kiểm thử JS dùng DOM fixture, không thay thế kiểm tra trực quan.
