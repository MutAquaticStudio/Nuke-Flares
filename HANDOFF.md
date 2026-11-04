# BÀN GIAO — Plugin lens flare "OpenFlares" cho Nuke — 2026-11-04

## Mục tiêu
Plugin lens flare tự viết (thay Optical Flares của Video Copilot đã dừng phát triển) chạy ổn trên Nuke 14+, không phụ thuộc minor version, tùy chỉnh được. Giai đoạn hiện tại: v0.2.0 đã xong và nằm trên GitHub; chờ người dùng chạy thử trong Nuke thật.

## Bối cảnh
- Người dùng nói tiếng Việt, tài khoản GitHub MutAquaticStudio, dùng Nuke, dùng cá nhân, không thương mại.
- Ban đầu người dùng gửi file RAR Optical Flares for Nuke 1.0.86 (qua Google Drive): chỉ có file nhị phân .so/.dll/.dylib cho Nuke 12-13, license mã hóa, ~780 preset .ofp, KHÔNG có mã nguồn.
- Phần phát triển được làm trong phiên Claude Code trên đám mây, không có Nuke thật.

## Đã làm xong
- Repo https://github.com/MutAquaticStudio/Nuke-Flares, nhánh main (commit đầu 75c4bb7 "OpenFlares v0.2.0").
- Nội dung:
  - `Kernels/OF_Flare.blink`: kernel Blink chính (3 glow, streak, starburst, 8 ghost/iris, flicker/pulse/spin, input `dirt` và `aperture`). SINH RA từ `tools/gen_kernel.py`, không sửa tay.
  - `Kernels/OF_AnamorphicStreak.blink`: streak tách từ độ sáng ảnh nguồn.
  - `of_core.py` (preset <-> tham số, bố cục tab, không phụ thuộc Nuke), `of_nuke.py` (dựng gizmo dạng Group 8 tab, menu), `menu.py` (chỉ gọi of_nuke).
  - `Presets/*.json`: 25 preset tự thiết kế (5 có animation), định dạng JSON riêng.
  - `reference/flare.py` (bộ render numpy làm chuẩn), `tests/` (run_kernel_test.py, run_texture_test.py, test_menu_mock.py, shim C++ giả lập Blink), `previews/kernel/` (ảnh render thử).
  - `README.md` tiếng Việt: yêu cầu, cài đặt Windows/macOS/Linux (init.py + nuke.pluginAddPath), cập nhật/gỡ, xử lý sự cố, danh sách tab/knob.
- Đã kiểm tra bằng máy: kernel qua shim C++ khớp numpy cả 25 preset (sai số < 0.01, kể cả animation); dirt/aperture chạy đúng, chưa nối input thì không lỗi; gizmo và preset round-trip đúng trên Nuke giả lập; 119 tham số kernel khớp tên knob.

## Quyết định đã chốt (không bàn lại)
- Dùng Blink Script, không viết C++ NDK: mã nguồn do Nuke biên dịch lúc chạy nên không ràng buộc theo minor version. Chỉ kiểm tra MAJOR (>= 14), chỉ cảnh báo, không chặn.
- KHÔNG dịch ngược/vá file nhị phân Optical Flares, KHÔNG giải mã định dạng .ofp, KHÔNG dùng lại preset/texture của Video Copilot (bản quyền, license node-locked). Preset phải tự viết; có thể dựng lại "cảm giác" kiểu flare bằng tham số riêng nếu người dùng mô tả hoặc đưa ảnh render của chính họ.
- Trong phiên Claude Code, `gh repo create` (GraphQL) không dùng được. Người dùng tự tạo repo rồi cấp quyền qua tool add_repo; PR và merge làm bằng REST API (`gh api`).

## Quy tắc / sở thích của người dùng
- Trả lời tiếng Việt, ngắn gọn, nói rõ cái gì đã kiểm tra được và cái gì chưa.
- Muốn dự án dùng cá nhân, tùy chỉnh được, dễ cài.
- Đã hỏi nhiều lần về việc dùng .ofp / preset Video Copilot; giữ nguyên quyết định ở trên, giải thích ngắn.

## Còn bỏ ngỏ / cần hỏi lại
- CHƯA chạy trong Nuke thật. Có thể cần chỉnh: cú pháp Blink mà shim C++ không bắt được (kiểu `bool` làm param, `src.bounds.x1`, ...), cách Nuke xử lý Link_Knob trên Group, tốc độ GPU ở 4K. Chờ người dùng gửi nguyên văn lỗi và số phiên bản Nuke.
- Repo đang public, chưa có file LICENSE (mặc định bảo lưu mọi quyền). Hỏi người dùng muốn giữ public hay đổi private, và có muốn thêm giấy phép (vd MIT) không.
- Hướng phát triển tiếp (nếu muốn): tối ưu tốc độ 4K, thêm preset (từ mô tả hoặc ảnh tham chiếu của chính người dùng), thêm hiệu ứng.

## Bước tiếp theo
1. Hỏi người dùng kết quả chạy thử trong Nuke thật (phiên bản Nuke, hệ điều hành, lỗi nếu có, nguyên văn).
2. Nếu có lỗi: clone repo, sửa `tools/gen_kernel.py` rồi chạy `python3 -I tools/gen_kernel.py` để sinh lại kernel; chạy lại 3 bài kiểm tra trong `tests/` (cần g++, numpy, Pillow); làm trên nhánh riêng, mở PR rồi merge.
3. Hỏi về public/private và LICENSE.
4. Làm tiếp các hướng ở mục "Còn bỏ ngỏ" theo yêu cầu.

## Tài liệu liên quan
- `README.md`: cài đặt, cách dùng, danh sách tab/knob, trạng thái kiểm thử.
- `previews/kernel/_contact_sheet.png`: ảnh tổng hợp 25 preset.
- File gốc Optical Flares (Google Drive người dùng đã chia sẻ): chỉ để tham khảo cấu trúc, không dùng nội dung.

## Lời nhắn cho AI tiếp nhận
Đọc hết bản bàn giao này, xác nhận ngắn là đã hiểu, rồi bắt đầu từ "Bước tiếp theo" số 1.
