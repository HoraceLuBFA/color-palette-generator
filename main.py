from PIL import Image, ImageDraw, ImageTk
import numpy as np
import tkinter as tk
from tkinter import filedialog, messagebox
import os

# ------------------------------
# Core image processing routine
# ------------------------------

def build_palette_bar(im: Image.Image, N=16, bar_h_ratio=0.09, bar_h_min=60, bar_h_max=200,
                      separator=2, border_px=2, bar_bg=(30, 30, 30),
                      sep_color=(220, 220, 220), border_color=(190, 190, 190),
                      sort_by_luma=True, swatch_aspect=None, method='MedianCut'):
    """
    Given a PIL image `im`, return (composite_image, palette_bar_image) where
    composite = original stacked over palette bar.
    """
    im = im.convert("RGB")
    w, h = im.size
    # Compute bar height from single-swatch aspect if provided
    if swatch_aspect:
        try:
            aspect = float(swatch_aspect)
        except Exception:
            aspect = None
        if aspect and aspect > 0:
            inner_w = max(1, w - 2 * border_px)
            total_separators = max(0, (N - 1) * separator)
            swatch_w = max(1, (inner_w - total_separators) // N)
            swatch_h = max(1, int(round(swatch_w / aspect)))
            bar_h = swatch_h + 2 * border_px
        else:
            bar_h = int(h * bar_h_ratio)
    else:
        bar_h = int(h * bar_h_ratio)
    # If swatch_aspect is specified, honor it fully (no upper cap). Capping to bar_h_max
    # can flatten swatches on wide images and break requested ratios like 1:1.
    if swatch_aspect:
        bar_h = max(2 * border_px + 1, int(bar_h))
    else:
        bar_h = min(max(int(bar_h), bar_h_min), bar_h_max)

    # Quantize / cluster to N colors according to method
    colors = []
    method = (method or 'MedianCut')
    if method == 'KMeans':
        # --- Simple numpy K-Means on RGB ---
        arr = np.array(im, dtype=np.uint8)
        flat = arr.reshape(-1, 3)
        # random sample to speed up
        max_sample = 50000
        if flat.shape[0] > max_sample:
            idx = np.random.choice(flat.shape[0], max_sample, replace=False)
            sample = flat[idx]
        else:
            sample = flat
        # init centers with random choices
        rng = np.random.default_rng(42)
        init_idx = rng.choice(sample.shape[0], min(N, sample.shape[0]), replace=False)
        centers = sample[init_idx].astype(np.float64)
        for _ in range(10):
            # assign
            d2 = ((sample[:, None, :] - centers[None, :, :]) ** 2).sum(axis=2)
            labels = d2.argmin(axis=1)
            # update
            new_centers = []
            for k in range(centers.shape[0]):
                pts = sample[labels == k]
                if len(pts) == 0:
                    # re-seed from data
                    new_centers.append(sample[rng.integers(0, sample.shape[0])])
                else:
                    new_centers.append(pts.mean(axis=0))
            centers = np.vstack(new_centers)
        # final assignment on full image for counts
        d2_full = ((flat[:, None, :] - centers[None, :, :]) ** 2).sum(axis=2)
        labels_full = d2_full.argmin(axis=1)
        for k in range(centers.shape[0]):
            cnt = int((labels_full == k).sum())
            r, g, b = [int(max(0, min(255, round(v)))) for v in centers[k]]
            colors.append(((r, g, b), cnt))
        # keep top-N by count
        colors.sort(key=lambda x: x[1], reverse=True)
        colors = colors[:N]
    else:
        # Pillow quantizers
        try:
            from PIL.Image import Quantize
            if method == 'FastOctree':
                q = im.quantize(colors=N, method=Quantize.FASTOCTREE)
            else:
                q = im.quantize(colors=N, method=Quantize.MEDIANCUT)
        except Exception:
            # fallback
            q = im.quantize(colors=N, method=Image.MEDIANCUT)
        palette = q.getpalette()[:256 * 3]
        idx_arr = np.array(q)
        unique, counts = np.unique(idx_arr, return_counts=True)
        count_map = dict(zip(unique.tolist(), counts.tolist()))
        for idx, cnt in count_map.items():
            r = palette[3 * idx + 0]
            g = palette[3 * idx + 1]
            b = palette[3 * idx + 2]
            colors.append(((r, g, b), int(cnt)))

    # Pad to N if needed using most frequent colors
    if 0 < len(colors) < N:
        colors_sorted_by_freq = sorted(colors, key=lambda x: x[1], reverse=True)
        while len(colors) < N:
            colors.append(colors_sorted_by_freq[len(colors) % len(colors_sorted_by_freq)])

    # Sort by luminance for a clean gradient-like arrangement
    if sort_by_luma:
        def luminance(rgb):
            r, g, b = rgb
            return 0.2126 * r + 0.7152 * g + 0.0722 * b
        colors = sorted(colors[:N], key=lambda x: luminance(x[0]))
    else:
        colors = colors[:N]

    # Draw palette bar
    bar = Image.new("RGB", (w, bar_h), bar_bg)
    draw = ImageDraw.Draw(bar)

    # Outer border
    draw.rectangle([0, 0, w - 1, bar_h - 1], outline=border_color, width=border_px)

    # Inner region
    inner_left = border_px
    inner_top = border_px
    inner_right = w - border_px
    inner_bottom = bar_h - border_px
    inner_w = inner_right - inner_left
    inner_h = inner_bottom - inner_top

    # Recompute swatch_h from swatch_aspect so the inner height matches exactly
    if swatch_aspect:
        try:
            aspect = float(swatch_aspect)
        except Exception:
            aspect = None
    else:
        aspect = None
    total_separators = (N - 1) * separator
    swatch_w = max(1, (inner_w - total_separators) // N)
    if aspect and aspect > 0:
        swatch_h = max(1, int(round(swatch_w / aspect)))
        inner_bottom = inner_top + swatch_h
        if inner_bottom > bar_h - border_px:
            inner_bottom = bar_h - border_px
    x = inner_left
    for i, (rgb, _cnt) in enumerate(colors):
        if i == N - 1:
            sw_right = inner_right
        else:
            sw_right = x + swatch_w
        draw.rectangle([x, inner_top, sw_right, inner_bottom], fill=tuple(rgb))
        if i != N - 1 and separator > 0:
            draw.rectangle([sw_right, inner_top, sw_right + separator - 1, inner_bottom], fill=sep_color)
        x = sw_right + separator

    # Compose final image (original on top, bar at bottom)
    out = Image.new("RGB", (w, h + bar_h), (0, 0, 0))
    out.paste(im, (0, 0))
    out.paste(bar, (0, h))

    return out, bar


# ------------------------------
# GUI
# ------------------------------

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("调色盘横条生成器 | Palette Bar Generator")
        self._refresh_job = None
        self.PREVIEW_MAXSIDE = 1400  # Max long side for preview computation

        # State
        self.src_image = None          # Original PIL image
        self.preview_image = None      # Composite PIL image for display
        self.tk_preview = None         # Tk PhotoImage reference to avoid GC
        self.current_path = None

        # Controls (left)
        ctrl = tk.Frame(self)
        ctrl.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        # File selection
        tk.Button(ctrl, text="选择图片…", command=self.choose_image).pack(fill=tk.X)
        self.path_label = tk.Label(ctrl, text="未选择", wraplength=260, anchor='w', justify='left')
        self.path_label.pack(fill=tk.X, pady=(4, 8))

        # Params
        self.N_var = tk.IntVar(value=16)
        self.sep_var = tk.IntVar(value=2)
        self.border_var = tk.IntVar(value=2)
        self.sort_var = tk.BooleanVar(value=True)
        # palette method & aspect ratio
        self.method_var = tk.StringVar(value="MedianCut")
        self.saspect_var = tk.StringVar(value="1:1")

        self._add_labeled_spin(ctrl, "色块数量 N", self.N_var, 3, 32, 1)
        # 生成方法
        mf = tk.Frame(ctrl)
        mf.pack(fill=tk.X, pady=2)
        tk.Label(mf, text="生成方法", width=14, anchor='w').pack(side=tk.LEFT)
        tk.OptionMenu(mf, self.method_var, "MedianCut", "FastOctree", "KMeans", command=lambda *_: self._request_preview()).pack(side=tk.LEFT, fill=tk.X, expand=True)
        # 色块宽高比（W:H）
        af = tk.Frame(ctrl)
        af.pack(fill=tk.X, pady=2)
        tk.Label(af, text="色块宽高比", width=14, anchor='w').pack(side=tk.LEFT)
        tk.OptionMenu(af, self.saspect_var, "5:4", "4:3", "3:2", "1:1", "2:3", "3:4", "4:5", command=lambda *_: self._request_preview()).pack(side=tk.LEFT, fill=tk.X, expand=True)
        # 导出格式
        self.export_format_var = tk.StringVar(value="JPEG")

        self._add_labeled_spin(ctrl, "分隔线(px)", self.sep_var, 0, 8, 1)
        self._add_labeled_spin(ctrl, "外边框(px)", self.border_var, 0, 8, 1)

        tk.Checkbutton(ctrl, text="按亮度从暗到亮排序", variable=self.sort_var, command=self._request_preview).pack(anchor='w', pady=(6, 10))

        self.export_scale_var = tk.IntVar(value=100)   # 导出缩放百分比（仅JPEG）
        self.jpeg_quality_var = tk.IntVar(value=100)   # JPEG质量（1-100）

        # 导出设置（JPEG）
        sep = tk.Frame(ctrl, height=1, bg="#ddd")
        sep.pack(fill=tk.X, pady=(8,6))

        # 导出设置行（包含导出格式下拉）
        self.settings_row = tk.Frame(ctrl)
        self.settings_row.pack(fill=tk.X)
        tk.Label(self.settings_row, text="导出格式", width=14, anchor='w').pack(side=tk.LEFT)
        tk.OptionMenu(self.settings_row, self.export_format_var, "JPEG", "PNG", command=lambda *_: self._on_export_format_change()).pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 导出模式（放在导出缩放之上）
        self.export_mode_var = tk.StringVar(value="percent")  # percent | longedge
        self.long_edge_var = tk.IntVar(value=2048)

        self.mode_row = tk.Frame(ctrl)
        self.mode_row.pack(fill=tk.X, pady=(4,2))
        tk.Label(self.mode_row, text="缩放模式", width=14, anchor='w').pack(side=tk.LEFT)
        modes = tk.Frame(self.mode_row)
        modes.pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Radiobutton(modes, text="百分比", value="percent", variable=self.export_mode_var, command=self._on_export_mode_change).pack(side=tk.LEFT)
        tk.Radiobutton(modes, text="长边像素", value="longedge", variable=self.export_mode_var, command=self._on_export_mode_change).pack(side=tk.LEFT)

        # 具体像素参数（仅长边像素）
        self.longedge_row = tk.Frame(ctrl)
        self.longedge_row.pack(fill=tk.X, pady=2)
        tk.Label(self.longedge_row, text="长边像素", width=14, anchor='w').pack(side=tk.LEFT)
        tk.Spinbox(self.longedge_row, from_=256, to=12000, textvariable=self.long_edge_var, increment=64, width=8, command=self._update_export_dim).pack(side=tk.LEFT)

        # 导出缩放与质量滑块
        self.export_scale_row = self._add_labeled_scale(ctrl, "导出缩放(%)", self.export_scale_var, 25, 200, 5, fmt="{:.0f}", affects_preview=False)
        # 导出尺寸显示（移动到导出缩放条下方）
        self.export_dim_label = tk.Label(ctrl, text="导出尺寸：—", anchor='w')
        self.export_dim_label.pack(fill=tk.X, pady=(6,0))
        # JPEG 质量（可能被隐藏）
        self.jpeg_quality_row = self._add_labeled_scale(ctrl, "JPEG质量", self.jpeg_quality_var, 0, 100, 1, fmt="{:.0f}", affects_preview=False)

        # PNG 选项
        self.png_compress_var = tk.IntVar(value=6)
        # self.png_label = tk.Label(ctrl, text="PNG 选项", anchor='w')
        self.png_compress_row = self._add_labeled_scale(ctrl, "压缩等级(0-9)", self.png_compress_var, 0, 9, 1, fmt="{:.0f}", affects_preview=False)

        # 操作按钮
        self.btns_frame = tk.Frame(ctrl)
        self.btns_frame.pack(fill=tk.X, pady=(8,6))
        tk.Button(self.btns_frame, text="预览/刷新", command=self.refresh_preview).pack(side=tk.LEFT, expand=True, fill=tk.X)
        tk.Button(self.btns_frame, text="保存成品…", command=self.save_composite).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(6, 0))

        # 独立的“保存仅色条…”按钮
        tk.Button(ctrl, text="保存仅色条…", command=self.save_bar).pack(fill=tk.X)

        # Preview (right)
        prev = tk.Frame(self)
        prev.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self.canvas = tk.Canvas(prev, background="#222")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<Configure>", lambda e: self._draw_preview())

        # 初始化导出模式与格式相关控件的可见性
        self._on_export_mode_change()
        self._on_export_format_change()

    # ----- UI helpers -----
    def _add_labeled_spin(self, parent, label, var, frm, to, step):
        f = tk.Frame(parent)
        f.pack(fill=tk.X, pady=2)
        tk.Label(f, text=label, width=14, anchor='w').pack(side=tk.LEFT)
        sb = tk.Spinbox(f, from_=frm, to=to, textvariable=var, increment=step, width=7, command=self._request_preview)
        sb.pack(side=tk.LEFT)

    def _add_labeled_scale(self, parent, label, var, frm, to, res, fmt="{:.2f}", affects_preview=True):
        f = tk.Frame(parent)
        f.pack(fill=tk.X, pady=2)
        top = tk.Frame(f)
        top.pack(fill=tk.X)
        tk.Label(top, text=label, anchor='w').pack(side=tk.LEFT)
        val_lbl = tk.Label(top, text=fmt.format(var.get()), anchor='e')
        val_lbl.pack(side=tk.RIGHT)
        if affects_preview:
            cmd = lambda _=None: (val_lbl.config(text=fmt.format(var.get())), self._request_preview())
        else:
            cmd = lambda _=None: (val_lbl.config(text=fmt.format(var.get())), self._update_export_dim())
        s = tk.Scale(f, from_=frm, to=to, resolution=res, orient=tk.HORIZONTAL, variable=var, command=cmd)
        s.pack(fill=tk.X)
        return f

    def _on_export_format_change(self):
        fmt = self.export_format_var.get()
        # 先隐藏所有相关控件
        try:
            if hasattr(self, 'jpeg_quality_row') and self.jpeg_quality_row is not None:
                self.jpeg_quality_row.pack_forget()
        except Exception:
            pass
        for w in ('png_label', 'png_compress_row'):
            try:
                ww = getattr(self, w, None)
                if ww is not None:
                    ww.pack_forget()
            except Exception:
                pass
        try:
            if hasattr(self, 'fmt_spacer_row') and self.fmt_spacer_row is not None:
                self.fmt_spacer_row.pack_forget()
        except Exception:
            pass
        # 再按顺序显示需要的控件（保证位置在按钮上方，且相对顺序稳定）
        if fmt == 'JPEG':
            if hasattr(self, 'jpeg_quality_row') and self.jpeg_quality_row is not None:
                try:
                    self.jpeg_quality_row.pack(before=self.mode_row, fill=tk.X, pady=(8,0))
                except Exception:
                    self.jpeg_quality_row.pack(fill=tk.X, pady=(8,0))
        else:  # PNG
            if hasattr(self, 'png_label') and self.png_label is not None:
                try:
                    self.png_label.pack(before=self.mode_row, fill=tk.X, pady=(8,0))
                except Exception:
                    self.png_label.pack(fill=tk.X, pady=(8,0))
            if hasattr(self, 'png_compress_row') and self.png_compress_row is not None:
                try:
                    self.png_compress_row.pack(before=self.mode_row, fill=tk.X, pady=2)
                except Exception:
                    self.png_compress_row.pack(fill=tk.X, pady=2)
            # 无优化选项
        
    def _on_export_mode_change(self):
        mode = self.export_mode_var.get()
        # 统一先隐藏两组控件
        try:
            if hasattr(self, 'export_scale_row') and self.export_scale_row is not None:
                self.export_scale_row.pack_forget()
        except Exception:
            pass
        try:
            if hasattr(self, 'longedge_row') and self.longedge_row is not None:
                self.longedge_row.pack_forget()
        except Exception:
            pass
        # 按模式显示对应控件，并放在导出尺寸标签之前，保证顺序
        if mode == 'percent':
            try:
                self.export_scale_row.pack(before=self.export_dim_label, fill=tk.X, pady=2)
            except Exception:
                self.export_scale_row.pack(fill=tk.X, pady=2)
        else:  # longedge
            try:
                self.longedge_row.pack(before=self.export_dim_label, fill=tk.X, pady=2)
            except Exception:
                self.longedge_row.pack(fill=tk.X, pady=2)
        # 更新尺寸显示
        self._update_export_dim()
    def _request_preview(self):
        if self._refresh_job is not None:
            try:
                self.after_cancel(self._refresh_job)
            except Exception:
                pass
        self._refresh_job = self.after(120, self.refresh_preview)

    def _update_export_dim(self):
        if self.preview_image is None:
            return
        ew, eh = self._compute_export_size(self.preview_image.width, self.preview_image.height)
        self.export_dim_label.config(text=f"导出尺寸：{ew}×{eh}px")

    def _make_preview_source(self) -> Image.Image:
        im = self.src_image
        if im is None:
            return None
        w, h = im.size
        long_side = max(w, h)
        scale = min(self.PREVIEW_MAXSIDE / float(long_side), 1.0)
        if scale < 1.0:
            nw = max(1, int(round(w * scale)))
            nh = max(1, int(round(h * scale)))
            return im.resize((nw, nh), Image.LANCZOS)
        return im

    def _parse_aspect(self, s: str) -> float:
        try:
            if ":" in s:
                a, b = s.split(":", 1)
                a = float(a.strip()); b = float(b.strip())
                return a / b if b != 0 else float(a)
            return float(s)
        except Exception:
            return 10.0  # fallback

    def _compute_export_size(self, base_w: int, base_h: int):
        mode = self.export_mode_var.get()
        if mode == 'percent':
            scale = max(1, int(self.export_scale_var.get())) / 100.0
        elif mode == 'longedge':
            le = max(1, int(self.long_edge_var.get()))
            scale = le / max(base_w, base_h)
        else:
            scale = 1.0
        nw = max(1, int(round(base_w * scale)))
        nh = max(1, int(round(base_h * scale)))
        return nw, nh

    def _resize_for_export(self, img: Image.Image) -> Image.Image:
        w, h = img.size
        nw, nh = self._compute_export_size(w, h)
        if (nw, nh) != (w, h):
            return img.resize((nw, nh), Image.LANCZOS)
        return img

    # ----- Actions -----
    def choose_image(self):
        path = filedialog.askopenfilename(title="选择图片", filetypes=[
            ("Image Files", "*.png *.jpg *.jpeg *.bmp *.tif *.tiff"),
            ("All Files", "*.*"),
        ])
        if not path:
            return
        try:
            self.src_image = Image.open(path).convert("RGB")
            self.current_path = path
            self.path_label.config(text=path)
            self.refresh_preview()
        except Exception as e:
            messagebox.showerror("读取失败", f"无法打开图片：\n{e}")

    def refresh_preview(self):
        if self.src_image is None:
            return
        try:
            src = self._make_preview_source()
            out, _bar = build_palette_bar(
                src,
                N=int(self.N_var.get()),
                swatch_aspect=self._parse_aspect(self.saspect_var.get()),
                separator=int(self.sep_var.get()),
                border_px=int(self.border_var.get()),
                sort_by_luma=bool(self.sort_var.get()),
                method=self.method_var.get(),
            )
            self.preview_image = out
            self._update_export_dim()
            self._draw_preview()
            self._refresh_job = None
        except Exception as e:
            messagebox.showerror("处理失败", str(e))

    def _draw_preview(self):
        if self.preview_image is None:
            self.canvas.delete("all")
            return
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        if cw < 2 or ch < 2:
            return
        # Fit preview to canvas while preserving aspect
        img = self.preview_image
        iw, ih = img.size
        scale = min(cw / iw, ch / ih)
        pw = max(1, int(iw * scale))
        ph = max(1, int(ih * scale))
        disp = img.resize((pw, ph), Image.LANCZOS)
        self.tk_preview = ImageTk.PhotoImage(disp)
        self.canvas.delete("all")
        self.canvas.create_image(cw // 2, ch // 2, image=self.tk_preview)

    def save_composite(self):
        if self.preview_image is None:
            messagebox.showinfo("提示", "请先选择图片并生成预览。")
            return
        default = "output_with_palette.jpg"
        if self.current_path:
            base = os.path.splitext(os.path.basename(self.current_path))[0]
            default = f"{base}_with_palette.jpg"
        fmt = self.export_format_var.get()
        if fmt == "PNG":
            defext = ".png"; ftypes = [("PNG", ".png"), ("All Files", "*.*")]
        else:
            defext = ".jpg"; ftypes = [("JPEG", ".jpg"), ("PNG", ".png"), ("All Files", "*.*")]
        path = filedialog.asksaveasfilename(title="保存成品", defaultextension=defext,
                                            initialfile=default, filetypes=ftypes)
        if not path:
            return
        try:
            # Recompute at full quality using current params on original (not the resized preview)
            out, _ = build_palette_bar(
                self.src_image,
                N=int(self.N_var.get()),
                swatch_aspect=self._parse_aspect(self.saspect_var.get()),
                separator=int(self.sep_var.get()),
                border_px=int(self.border_var.get()),
                sort_by_luma=bool(self.sort_var.get()),
                method=self.method_var.get(),
            )
            ext = os.path.splitext(path)[1].lower()
            out = self._resize_for_export(out)
            if ext in (".jpg", ".jpeg"):
                out.save(path, quality=int(self.jpeg_quality_var.get()))
            elif ext == ".png":
                cl = max(0, min(9, int(self.png_compress_var.get())))
                out.save(path, compress_level=cl)
            else:
                out.save(path)
            messagebox.showinfo("已保存", path)
        except Exception as e:
            messagebox.showerror("保存失败", str(e))

    def save_bar(self):
        if self.src_image is None:
            messagebox.showinfo("提示", "请先选择图片并生成预览。")
            return
        default = "palette_bar.png"
        if self.current_path:
            base = os.path.splitext(os.path.basename(self.current_path))[0]
            default = f"{base}_palette_bar.png"
        fmt = self.export_format_var.get()
        if fmt == "PNG":
            defext = ".png"; ftypes = [("PNG", ".png"), ("All Files", "*.*")]
        else:
            defext = ".jpg"; ftypes = [("JPEG", ".jpg"), ("PNG", ".png"), ("All Files", "*.*")]
        path = filedialog.asksaveasfilename(title="保存仅色条", defaultextension=defext,
                                            initialfile=default, filetypes=ftypes)
        if not path:
            return
        try:
            _out, bar = build_palette_bar(
                self.src_image,
                N=int(self.N_var.get()),
                swatch_aspect=self._parse_aspect(self.saspect_var.get()),
                separator=int(self.sep_var.get()),
                border_px=int(self.border_var.get()),
                sort_by_luma=bool(self.sort_var.get()),
                method=self.method_var.get(),
            )
            ext = os.path.splitext(path)[1].lower()
            bar = self._resize_for_export(bar)
            if ext in (".jpg", ".jpeg"):
                bar.save(path, quality=int(self.jpeg_quality_var.get()))
            elif ext == ".png":
                cl = max(0, min(9, int(self.png_compress_var.get())))
                bar.save(path, compress_level=cl)
            else:
                bar.save(path)
            messagebox.showinfo("已保存", path)
        except Exception as e:
            messagebox.showerror("保存失败", str(e))


if __name__ == "__main__":
    app = App()
    app.geometry("1200x700")
    app.mainloop()
