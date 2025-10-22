# Color Palette Generator（调色盘横条生成器）

[中文](#中文) | [English](#english)

---

## 中文

Color Palette Generator 是一款使用 Python + Tkinter 构建的桌面小工具，可从任意图片中提取代表性颜色并生成“调色盘横条”，支持与原图上下合成输出，或仅导出色条。提供多种颜色量化方法、色块样式与导出选项，满足设计、摄影与配色分析等场景需求。

### 功能特性

- 图像导入与预览
  - 通过文件对话框选择图片（PNG/JPG/JPEG/BMP/TIFF）。
  - 右侧画布自适应预览，参数修改后可一键刷新。
- 调色盘生成
  - 可选颜色数量 `N`（3–32）。
  - 颜色提取方法：MedianCut、FastOctree、KMeans（基于 NumPy，较慢但可对比效果）。
  - 可按相对亮度排序（从暗到亮），形成更平滑的视觉过渡。
- 色块样式
  - 色块宽高比（W:H）：5:4、4:3、3:2、1:1、2:3、3:4、4:5。
  - 分隔线与外边框像素可调，支持自定义条形风格。
- 导出与尺寸控制
  - 保存合成图（原图在上、色条在下）或“仅色条”。
  - 导出格式：JPEG 或 PNG。
  - 缩放模式：按百分比或设定“长边像素”。
  - JPEG 质量（0–100）、PNG 压缩等级（0–9）。

### 快速上手（预编译版，macOS）

如果本仓库已在 GitHub Releases 提供预编译应用：

1. 前往项目 Releases 页面。
2. 下载 `ColorPaletteGenerator.app`（或压缩包），解压后双击运行。
3. 首次运行如遇安全提示，可使用右键“打开”或在“系统设置 → 安全性与隐私”中允许来自已识别开发者的应用。

若未提供预编译包，请参考下方“从源码运行/构建”。

### 从源码运行

- 环境要求
  - Python 3.10+
  - Pillow、NumPy（Tkinter 随多数 Python 发行版一并提供）

- 安装依赖（建议虚拟环境）

  ```bash
  python3 -m venv .venv
  source .venv/bin/activate   # Windows 使用 .venv\Scripts\activate
  python3 -m pip install --upgrade pip
  pip install pillow numpy
  ```

- 运行

  ```bash
  python3 main.py
  ```

### 使用说明

1. 选择图片：点击“选择图片…”。
2. 设置参数：
   - 色块数量 N、生成方法（MedianCut/FastOctree/KMeans）。
   - 色块宽高比、分隔线像素、外边框像素。
   - “按亮度从暗到亮排序”以优化视觉顺序。
   - 导出格式（JPEG/PNG）、缩放模式（百分比/长边像素）、JPEG 质量或 PNG 压缩等级。
3. 预览/刷新：点击“预览/刷新”查看效果。
4. 导出：
   - “保存成品…” 输出合成图（原图+色条）。
   - “保存仅色条…” 仅输出色条图像。

提示：预览默认对长边做限制以提升交互流畅度，最终导出会基于原图重新计算并按导出缩放设置进行高质量重采样。

### 许可证

本项目采用 MIT 许可证（MIT License）。如需分发，请在发布包中附带 LICENSE 文件。

---

## English

Color Palette Generator is a lightweight desktop tool built with Python and Tkinter. It extracts representative colors from an image to create a horizontal “palette bar”, and lets you export either the composite (original on top + palette bar at bottom) or the palette bar alone. It provides multiple quantization methods, swatch styling, and flexible export controls.

### Features

- Import & Preview
  - Pick an image via file dialog (PNG/JPG/JPEG/BMP/TIFF).
  - Responsive canvas preview; refresh after adjusting parameters.
- Palette Generation
  - Adjustable color count `N` (3–32).
  - Methods: MedianCut, FastOctree, KMeans (NumPy-based; slower but useful for comparison).
  - Optional luminance-based ordering (dark → light) for smoother visual flow.
- Swatch Styling
  - Swatch aspect ratio (W:H): 5:4, 4:3, 3:2, 1:1, 2:3, 3:4, 4:5.
  - Adjustable separator and outer border in pixels.
- Export & Sizing
  - Export composite image or palette bar only.
  - Formats: JPEG or PNG.
  - Scaling modes: percentage or fixed long-edge pixels.
  - JPEG quality (0–100), PNG compression level (0–9).

### Quick Start (Prebuilt, macOS)

If a prebuilt app is available on the project’s Releases page:

1. Download `ColorPaletteGenerator.app` (or the archive) and unzip.
2. Double-click to run. On first launch, you may need to right-click → Open, or allow apps from identified developers in System Settings.

If no prebuilt is provided, see the sections below to run from source or build locally.

### Run From Source

- Requirements
  - Python 3.10+
  - Pillow, NumPy (Tkinter ships with most Python distributions)

- Install dependencies (virtualenv recommended)

  ```bash
  python3 -m venv .venv
  source .venv/bin/activate   # On Windows: .venv\Scripts\activate
  python3 -m pip install --upgrade pip
  pip install pillow numpy
  ```

- Run

  ```bash
  python3 main.py
  ```

### Usage

1. Choose an image via “选择图片…”.
2. Tune parameters:
   - Color count N, method (MedianCut/FastOctree/KMeans).
   - Swatch aspect ratio, separator width, outer border.
   - Luminance sort (dark → light) for better ordering.
   - Export format (JPEG/PNG), scaling (percent/long-edge), and JPEG/PNG quality settings.
3. Preview/Refresh to update the preview.
4. Export:
   - “保存成品…” to export composite (original + palette bar).
   - “保存仅色条…” to export the palette bar only.

Note: The preview is downscaled for responsiveness; the final export is recomputed from the original at the chosen output scale for best quality.

### License

MIT License. Include a LICENSE file in distributions where applicable.

---

## 开发与贡献（可选）/ Contributing (Optional)

- 开发环境建议 Python 3.10+，提交前请自测运行 `python3 main.py`。
- 打包前建议使用 `pyinstaller --clean` 以获得可复现产物。
- 欢迎提交 Issue/PR 以改进功能与交互体验。
