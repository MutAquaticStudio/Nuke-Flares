# OpenFlares v0.2.0

Plugin lens flare tự viết từ đầu cho Nuke 14+ (Python 3), bằng Blink Script (chạy GPU).
Dùng cá nhân, không chứa code, preset hay texture của Optical Flares / Video Copilot.

## Yêu cầu
- Nuke **14 trở lên** (Python 3). Bản minor/patch nào cũng dùng chung một plugin.
- Node `BlinkScript` có trong bản Nuke của bạn (chạy được trên CPU, nhanh hơn nếu có GPU).
- Không cần compiler, không cần NDK.

## Cài đặt

**Bước 1. Tải về.** Tải ZIP của repo (nút **Code > Download ZIP**) hoặc clone:

    git clone <duong-dan-repo> OpenFlares

Đặt thư mục `OpenFlares` ở chỗ cố định, ví dụ:

| Hệ điều hành | Ví dụ vị trí |
|---|---|
| Windows | `C:\Users\TEN_BAN\.nuke\OpenFlares` |
| macOS | `/Users/TEN_BAN/.nuke/OpenFlares` |
| Linux | `/home/TEN_BAN/.nuke/OpenFlares` |

Thư mục này phải chứa trực tiếp `menu.py`, `of_core.py`, `of_nuke.py`, `Kernels/`, `Presets/`
(nếu giải nén ra thêm một lớp thư mục `OpenFlares/OpenFlares/` thì trỏ vào lớp trong cùng).

**Bước 2. Khai báo với Nuke.** Mở (hoặc tạo) file `init.py` trong thư mục `.nuke` của bạn:

| Hệ điều hành | File |
|---|---|
| Windows | `C:\Users\TEN_BAN\.nuke\init.py` |
| macOS / Linux | `~/.nuke/init.py` |

Thêm vào cuối file:

    import nuke
    nuke.pluginAddPath("C:/Users/TEN_BAN/.nuke/OpenFlares")    # sửa thành đường dẫn của bạn

Trên Windows hãy dùng dấu `/` trong đường dẫn. Nếu muốn dùng dấu `\`, phải viết gấp đôi thành `\\`.

**Bước 3. Khởi động lại Nuke.** Trên thanh menu **Nodes** sẽ có mục **OpenFlares**.

**Bước 4. Thử.** Nodes > OpenFlares > **New Flare**. Nếu chọn một node ảnh trước đó, flare tự nối vào input `src`.
Lần đầu Nuke biên dịch kernel nên có thể đợi một lúc.

### Cập nhật / gỡ cài đặt
- Cập nhật: thay nội dung thư mục `OpenFlares` bằng bản mới (preset riêng của bạn ở `~/.nuke/OpenFlares_Presets/` không bị mất).
  Script cũ vẫn mở được vì gizmo lưu nguyên kernel trong file `.nk`.
- Gỡ: xóa dòng `pluginAddPath` trong `init.py`, rồi xóa thư mục `OpenFlares`.

### Xử lý sự cố
| Hiện tượng | Cách xử lý |
|---|---|
| Không thấy menu OpenFlares | Kiểm tra đường dẫn trong `init.py`, xem tab Script Editor / terminal có báo lỗi `ModuleNotFoundError: of_core` không (thường do trỏ nhầm thư mục). |
| Báo lỗi khi tạo node hoặc khi recompile | Gửi nguyên văn lỗi (kèm số phiên bản Nuke) vào mục Issues của repo. |
| Flare không thấy | Light Position nằm ngoài khung, hoặc Master / Intensity bằng 0. Tick **Flare Only** để xem riêng flare. |
| Chậm ở 4K | Giảm số thành phần đang bật (đặt Intensity = 0 cho glow, ghost không cần), tắt Dirt. |

## Menu
- **New Flare** / **New Flare from Preset**: tạo gizmo `OF_Flare` (một Group có tab, bên trong là node BlinkScript).
- **New Flare with Textures...**: hỏi 2 file ảnh (tùy chọn) rồi tạo Read và nối vào input `dirt` / `aperture`.
- **Apply Preset to Selected Flare**, **Save Selected Flare as Preset...**
- **Anamorphic Streak (from source brightness)**: tách vùng sáng của chính ảnh nguồn rồi kéo thành streak.

## Gizmo OF_Flare
Input: `src` (nền), `dirt` (tùy chọn), `aperture` (tùy chọn). Output = nền + flare.

| Tab | Nội dung |
|---|---|
| Flare | Light Position (kéo trên viewer hoặc link Tracker), Master Intensity, Flare Scale, Ghost Spread, Follow Source Brightness, Global Tint, Flare Only |
| Glow | 3 lớp: Radius, Intensity, Color, Halo |
| Streak & Star | Streak (Length, Thickness, Intensity, Color, Angle); Starburst (Rays, Length, Intensity, Color, Sharpness, Rotation, Seed) |
| Ghosts 1-4, 5-8 | Position, Size, Intensity, Color, Shape, Polygon Sides, Softness, Ring Width, Rim |
| Animation | Flicker, Ghost Flicker, Pulse, Spin, Polygon Rotation, Time Offset |
| Textures | Dirt Amount / Spread / Scale / Offset / Tint |
| Presets | danh sách preset, Apply, Save Current Look, Reload |

Một thành phần tắt khi Intensity = 0. Kích thước tính theo chiều cao ảnh nên preset dùng được ở mọi độ phân giải.

### Animation tự động
Tự chạy theo frame (không cần keyframe): **Flicker** nhấp nháy cường độ (Speed, Seed; Ghost Flicker làm từng ghost nhấp nháy lệch pha),
**Pulse** nhịp thở của kích thước, **Spin** xoay starburst (tùy chọn xoay cả streak và ghost đa giác). Time Offset dịch pha khi cần.

### Texture của riêng bạn
- **dirt**: nối ảnh bụi / vân / xước vào input `dirt`. Ảnh được co giãn phủ kín khung, và chỉ sáng lên ở vùng quanh glow
  (Dirt Spread = độ rộng vùng chiếu sáng, Scale / Offset để căn lại, Tint để nhuộm màu). Kích thước ảnh bất kỳ.
- **aperture**: nối ảnh trắng trên nền đen (ngôi sao, trái tim, cánh hoa...) vào input `aperture`, rồi đặt
  **Shape = 3** cho ghost muốn dùng. Hình xoay theo Spin khi bật "Spin Polygon/Custom Ghosts".
- Input chưa nối thì bỏ qua, không gây lỗi.

## Preset
`Presets/*.json`: 25 preset (20 tĩnh, 5 có animation). Bạn tự chỉnh tay hoặc dùng **Save Current Look as Preset...**;
preset của bạn nằm ở `~/.nuke/OpenFlares_Presets/` và hiện luôn trong menu và dropdown.

## Tương thích phiên bản
Kernel Blink là mã nguồn do Nuke biên dịch lúc chạy, không có file nhị phân theo từng bản Nuke, nên các bản minor/patch dùng chung một plugin.
Code Python chỉ kiểm tra major (>= 14) và chỉ cảnh báo, không chặn. Gizmo lưu nguyên kernel trong file .nk.

## Cấu trúc
    Kernels/OF_Flare.blink            kernel chính (SINH RA từ tools/gen_kernel.py, đừng sửa tay)
    Kernels/OF_AnamorphicStreak.blink streak từ ảnh nguồn
    of_core.py                        preset <-> tham số, bố cục tab (không phụ thuộc Nuke)
    of_nuke.py, menu.py               dựng gizmo, menu Nuke
    reference/flare.py                bộ render numpy dùng để thiết kế preset và làm chuẩn so sánh
    tests/                            kiểm tra (xem dưới); previews/kernel/ là ảnh render thử

## Trạng thái kiểm thử
Đã kiểm tra bằng máy (không có Nuke):
- `tests/run_kernel_test.py`: kernel qua lớp giả lập C++ khớp bản numpy cho cả 25 preset, kể cả animation ở nhiều frame (sai số < 0.01).
- `tests/run_texture_test.py`: input dirt và aperture hoạt động; không nối input thì không lỗi.
- `tests/test_menu_mock.py`: dựng gizmo, nối input, link knob, lưu / nạp preset trên Nuke giả lập; đối chiếu 119 tham số với khai báo thật trong kernel.

**Chưa chạy trong Nuke thật.** Những chỗ có thể cần chỉnh sau lần chạy đầu: cú pháp Blink mà lớp giả lập C++ không bắt được,
cách Nuke xử lý `Link_Knob` trên Group, tốc độ GPU. Nếu có lỗi, gửi nguyên văn thông báo.
