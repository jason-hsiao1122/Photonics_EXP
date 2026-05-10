"""
Spot Size Analysis v2 — OpenCV Pipeline + Manual Calibration
=============================================================
Pipeline:
  1. Grayscale conversion
  2. Scale calibration (manual click / auto ruler detection / fixed value)
  3. Brightness gradient edge detection
  4. 50 scan lines -> diameter mean +/- std

Usage:
  CALIBRATION_MODE = "manual"   # interactive: click two ruler marks
  CALIBRATION_MODE = "auto"     # auto-detect cm tick marks on ruler
  CALIBRATION_MODE = "fixed"    # supply px/mm directly
=============================================================
"""

import cv2
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from scipy.ndimage import gaussian_filter1d
from scipy.signal import find_peaks
from scipy.optimize import curve_fit

# ═══════════════════════════════════════════════════════════════════
# ★ Config — adjust as needed
# ═══════════════════════════════════════════════════════════════════
IMG_PATH         = "DCV_5.jpg"
CALIBRATION_MODE = "fixed"     # "manual" | "auto" | "fixed"
KNOWN_MM         = 10.0       # manual mode: known distance between the two clicked points (mm)
FIXED_PX_PER_MM  = 34     # fixed mode: supply scale directly
N_LINES          = 50
SCAN_R           = 350        # scan radius (px) — needs to exceed spot radius

# Ruler crop: exclude pixels at or below this y from all scan lines.
# Set to None to disable (auto-detect from image height is NOT done — set manually).
# Prevents steep scan lines from crossing the ruler and corrupting the profile.
RULER_Y          = None       # e.g. 1185 for the new image; None = no mask

# Edge detection method for Gaussian beam profiles:
#   "fwhm"    — threshold at 50%  intensity  (most common beam width definition)
#   "1/e2"    — threshold at 13.5% intensity  (standard laser beam width)
#   "1/e"     — threshold at 36.8% intensity
#   "gauss"   — fit a Gaussian, report 2.355*sigma (FWHM) or 2*sqrt(2)*sigma (1/e²)
EDGE_METHOD      = "fwhm"     # "fwhm" | "1/e2" | "1/e" | "gauss"
RADIUS_DEV_MAX   = 3.5        # outlier filter: drop lines where |r - median_r| > this (mm)

# ═══════════════════════════════════════════════════════════════════
# 0. Load image
# ═══════════════════════════════════════════════════════════════════
img_bgr = cv2.imread(IMG_PATH)
img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
H, W    = img_rgb.shape[:2]
print(f"Image size: {W} x {H} px")

# ═══════════════════════════════════════════════════════════════════
# 1. Grayscale conversion
# ═══════════════════════════════════════════════════════════════════
gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
print("Step 1 — Grayscale conversion done")

# ═══════════════════════════════════════════════════════════════════
# 2. Scale calibration functions
# ═══════════════════════════════════════════════════════════════════

def calibrate_manual(img_rgb, known_mm):
    """Interactive: click two ruler marks to compute px/mm."""
    fig, ax = plt.subplots(figsize=(14, 10))
    fig.patch.set_facecolor('#111')
    ax.set_facecolor('#111')
    ax.imshow(img_rgb)

    ax.set_title(
        f"[Manual calibration]  Click two ruler marks {known_mm:.0f} mm apart\n"
        "Left-click to select, right-click to undo, then close window",
        color='white', fontsize=12, pad=10
    )

    inset_ax = fig.add_axes([0.55, 0.02, 0.43, 0.22])
    ruler_crop = img_rgb[900:1100, 400:1450]
    inset_ax.imshow(ruler_crop)
    inset_ax.set_title("Ruler close-up (reference)", color='white', fontsize=9)
    inset_ax.axis('off')

    plt.tight_layout()
    pts = plt.ginput(n=2, timeout=0, show_clicks=True)
    plt.close()

    if len(pts) != 2:
        raise RuntimeError("Two points not selected — calibration cancelled")

    (x1, y1), (x2, y2) = pts
    pixel_dist = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    px_per_mm  = pixel_dist / known_mm

    print(f"  Point 1: ({x1:.1f}, {y1:.1f})")
    print(f"  Point 2: ({x2:.1f}, {y2:.1f})")
    print(f"  Pixel distance: {pixel_dist:.2f} px  /  {known_mm} mm")
    print(f"  -> {px_per_mm:.4f} px/mm")

    return px_per_mm, [(x1, y1), (x2, y2)]


def calibrate_auto(gray):
    """Auto-detect cm tick peaks on ruler to compute px/mm.
    Tries decreasing peak-distance thresholds to find cm-level spacing first."""
    H_img, W_img = gray.shape
    best = None

    for frac in np.arange(0.60, 0.96, 0.02):
        ry1 = int(H_img * frac)
        ry2 = min(ry1 + 25, H_img)
        if ry2 <= ry1:
            continue
        ruler_roi = gray[ry1:ry2, 50:-50].astype(np.float64)
        col_var   = np.var(ruler_roi, axis=0)
        col_s     = gaussian_filter1d(col_var, sigma=2.0)

        # Try from large spacing down — largest valid = cm marks, stop at first good hit
        for dist in [int(W_img * 0.18), int(W_img * 0.12), int(W_img * 0.08), 80]:
            cm_peaks, _ = find_peaks(col_s,
                                      height=np.percentile(col_s, 85),
                                      distance=max(dist, 40))
            if len(cm_peaks) < 2:
                continue
            span_px   = int(cm_peaks[-1] - cm_peaks[0])
            span_mm   = (len(cm_peaks) - 1) * 10.0
            px_per_mm = span_px / span_mm
            if 5 < px_per_mm < 100:
                score = len(cm_peaks)
                if best is None or score > best[0]:
                    best = (score, px_per_mm, len(cm_peaks), span_px, span_mm,
                            cm_peaks + 50, ry1, ry2)
                break

    if best:
        _, px_per_mm, n_peaks, span_px, span_mm, cm_peaks_x, ry1, ry2 = best
        print(f"  Found {n_peaks} cm tick peaks spanning {span_px} px = {span_mm:.0f} mm"
              f"  (ruler strip y={ry1}-{ry2})")
        return px_per_mm, cm_peaks_x, ry1, ry2, 50

    fallback = 11.12
    print(f"  Auto calibration failed — using fallback {fallback} px/mm")
    return fallback, np.array([]), int(H_img*0.7), int(H_img*0.72), 50


# ── Run selected calibration mode ──────────────────────────────────
calib_pts   = None   # manual click points (for visualisation)
cm_peaks_x  = np.array([])
RULER_Y1_VIS, RULER_Y2_VIS, RULER_X1_VIS = 955, 970, 400

if CALIBRATION_MODE == "manual":
    print("Step 2 — [MANUAL] Scale calibration")
    PX_PER_MM, calib_pts = calibrate_manual(img_rgb, KNOWN_MM)

elif CALIBRATION_MODE == "auto":
    print("Step 2 — [AUTO] Scale calibration")
    PX_PER_MM, cm_peaks_x, RULER_Y1_VIS, RULER_Y2_VIS, RULER_X1_VIS = calibrate_auto(gray)

else:  # "fixed"
    PX_PER_MM = FIXED_PX_PER_MM
    print(f"Step 2 — [FIXED] Scale = {PX_PER_MM} px/mm")

MM_PER_PX = 1.0 / PX_PER_MM
print(f"Step 2 — Scale confirmed: {PX_PER_MM:.4f} px/mm")

# ═══════════════════════════════════════════════════════════════════
# 3a. 找光斑中心 (Green-enhanced)
# ═══════════════════════════════════════════════════════════════════
R = img_rgb[:, :, 0].astype(np.float32)
G = img_rgb[:, :, 1].astype(np.float32)
B = img_rgb[:, :, 2].astype(np.float32)

green_enh = np.clip(G - 0.45 * (R + B), 0, 255).astype(np.uint8)
blurred   = cv2.GaussianBlur(green_enh, (31, 31), 0)
_, _, _, cx_cy = cv2.minMaxLoc(blurred)
CX, CY = cx_cy
CX += -30
CY += 10
print(f"Step 3 — Spot centre: ({CX}, {CY})")

# ═══════════════════════════════════════════════════════════════════
# 3b. 亮度微分 + Canny 邊緣
# ═══════════════════════════════════════════════════════════════════
grad_x   = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
grad_y   = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
grad_mag = np.sqrt(grad_x**2 + grad_y**2)
grad_vis = (grad_mag / grad_mag.max() * 255).astype(np.uint8)

ROI_HALF = 180
rx1, rx2 = max(0, CX - ROI_HALF), min(W, CX + ROI_HALF)
ry1, ry2 = max(0, CY - ROI_HALF), min(H, CY + ROI_HALF)
gray_roi  = gray[ry1:ry2, rx1:rx2]
med_val   = float(np.median(gray_roi))
low_thr   = int(max(10,  0.67 * med_val))
high_thr  = int(min(245, 1.33 * med_val))
edges_roi = cv2.Canny(gray_roi, low_thr, high_thr)
edges_full = np.zeros_like(gray)
edges_full[ry1:ry2, rx1:rx2] = edges_roi
print("Step 3 — Gradient map & Canny edges done")

# ═══════════════════════════════════════════════════════════════════
# 4. 50 scan lines — Gaussian beam edge detection
# ═══════════════════════════════════════════════════════════════════

# threshold map for the three intensity methods
_THRESHOLDS = {"fwhm": 0.5, "1/e2": 1.0/np.e**2, "1/e": 1.0/np.e}

def _interp_cross(norm_profile, t_vals, threshold, idx, rising):
    """Sub-pixel linear interpolation of threshold crossing."""
    if rising and idx > 0:
        x0, x1 = t_vals[idx-1], t_vals[idx]
        y0, y1 = norm_profile[idx-1], norm_profile[idx]
    elif not rising and idx < len(t_vals) - 1:
        x0, x1 = t_vals[idx], t_vals[idx+1]
        y0, y1 = norm_profile[idx], norm_profile[idx+1]
    else:
        return t_vals[idx]
    if y1 == y0:
        return t_vals[idx]
    return float(x0 + (threshold - y0) * (x1 - x0) / (y1 - y0))

def measure_diameter(profile, t_v, method):
    """
    Returns (diam_px, t_left, t_right) or None if measurement fails.
    Profile is raw (not normalised). t_v are the corresponding positions.
    """
    p_smooth = gaussian_filter1d(profile.astype(float), sigma=3)
    bg   = np.percentile(p_smooth, 5)
    peak = p_smooth.max()
    if peak - bg < 20:
        return None

    if method == "gauss":
        # Fit I(t) = bg + A * exp(-0.5 * ((t-mu)/sigma)^2)
        def gauss_fn(x, A, mu, sigma, bg_):
            return bg_ + A * np.exp(-0.5 * ((x - mu) / sigma) ** 2)
        try:
            popt, _ = curve_fit(
                gauss_fn, t_v, p_smooth,
                p0=[peak - bg, float(t_v[len(t_v)//2]), 50.0, bg],
                bounds=([0, t_v.min(), 1, 0],
                        [np.inf, t_v.max(), SCAN_R, np.inf]),
                maxfev=4000
            )
            _, mu, sigma, _ = popt
            sigma = abs(sigma)
            half_fwhm = 1.1775 * sigma          # 2.355/2
            t_left  = mu - half_fwhm
            t_right = mu + half_fwhm
            diam_px = 2 * half_fwhm             # FWHM by default
        except Exception:
            return None
    else:
        threshold = _THRESHOLDS[method]
        norm = (p_smooth - bg) / (peak - bg)
        above = norm >= threshold
        if not above.any():
            return None
        idxs = np.where(above)[0]
        t_left  = _interp_cross(norm, t_v, threshold, idxs[0],   rising=True)
        t_right = _interp_cross(norm, t_v, threshold, idxs[-1],  rising=False)
        diam_px = t_right - t_left

    if diam_px < 10 or diam_px > 2 * SCAN_R - 10:
        return None
    return diam_px, t_left, t_right

# ── Run scan lines ──────────────────────────────────────────────────
angles         = np.linspace(0, np.pi, N_LINES, endpoint=False)
diameters_px   = []
line_endpoints = []
spot_channel   = green_enh.astype(np.float32)

for angle in angles:
    cos_a, sin_a = np.cos(angle), np.sin(angle)
    t_vals = np.arange(-SCAN_R, SCAN_R + 1, dtype=np.float32)

    xs = (CX + t_vals * cos_a).astype(int)
    ys = (CY + t_vals * sin_a).astype(int)
    valid = (xs >= 0) & (xs < W) & (ys >= 0) & (ys < H)
    if RULER_Y is not None:
        valid &= (ys < RULER_Y)   # clip scan line before it enters the ruler
    xs_v, ys_v, t_v = xs[valid], ys[valid], t_vals[valid]
    if len(t_v) < 30:
        continue

    result = measure_diameter(spot_channel[ys_v, xs_v], t_v, EDGE_METHOD)
    if result is None:
        continue

    diam_px, t_left, t_right = result
    diameters_px.append(diam_px)
    line_endpoints.append((
        (int(CX + t_left  * cos_a), int(CY + t_left  * sin_a)),
        (int(CX + t_right * cos_a), int(CY + t_right * sin_a))
    ))

diameters_px = np.array(diameters_px)
diameters_mm = diameters_px * MM_PER_PX

# ── Outlier filter: remove lines where |radius - median_radius| > 3.5 mm ──
RADIUS_DEV_MAX = 3.5
radii_mm       = diameters_mm / 2
median_radius  = np.median(radii_mm)
mask           = np.abs(radii_mm - median_radius) <= RADIUS_DEV_MAX
n_raw          = len(diameters_mm)
diameters_px   = diameters_px[mask]
diameters_mm   = diameters_mm[mask]
line_endpoints = [ep for ep, m in zip(line_endpoints, mask) if m]
n_filtered     = n_raw - len(diameters_mm)

mean_px, std_px = np.mean(diameters_px), np.std(diameters_px, ddof=1)
mean_mm, std_mm = np.mean(diameters_mm), np.std(diameters_mm, ddof=1)
median_mm       = np.median(diameters_mm)
cv_pct          = 100 * std_mm / mean_mm



print(f"\nStep 4 — Scan lines done ({len(diameters_px)}/{N_LINES} valid, method={EDGE_METHOD})")
print(f"         Outlier filter (|radius - median| > {RADIUS_DEV_MAX} mm): removed {n_filtered} lines")
print(f"\n{'='*50}")
print(f"  Calibration:  {CALIBRATION_MODE.upper()}")
print(f"  Edge method:  {EDGE_METHOD}")
print(f"  Scale:        {PX_PER_MM:.4f} px/mm")
print(f"  Mean diam:    {mean_mm:.3f} +/- {std_mm:.3f} mm")
print(f"  Median:       {median_mm:.3f} mm")
print(f"  CV%:          {cv_pct:.1f} %")
print(f"  Range:        {diameters_mm.min():.3f} ~ {diameters_mm.max():.3f} mm")
print(f"{'='*50}")

# ═══════════════════════════════════════════════════════════════════
# 5. 視覺化
# ═══════════════════════════════════════════════════════════════════
DARK_BG  = '#0d0d0d'
PANEL_BG = '#141414'
GRID_CLR = '#2a2a2a'
WHITE    = '#e8e8e8'

fig = plt.figure(figsize=(20, 13), facecolor=DARK_BG)
gs  = fig.add_gridspec(2, 3, wspace=0.06, hspace=0.24,
                        left=0.04, right=0.98, top=0.93, bottom=0.06)
axes = [fig.add_subplot(gs[r, c]) for r in range(2) for c in range(3)]
for ax in axes:
    ax.set_facecolor(PANEL_BG)
    for sp in ax.spines.values(): sp.set_edgecolor('#333')
plt.rcParams.update({'text.color': WHITE, 'axes.labelcolor': WHITE,
                     'xtick.color': WHITE, 'ytick.color': WHITE,
                     'axes.titlecolor': WHITE})

# ─── Panel 0: 原始圖 + 校正標記 ───
ax = axes[0]
ax.imshow(img_rgb)
ax.plot(CX, CY, 'r+', ms=16, mew=2.5)
if RULER_Y is not None:
    ax.axhline(RULER_Y, color='#FF6600', lw=1.5, ls='--', alpha=0.8, label=f'Ruler mask y={RULER_Y}')
    ax.legend(fontsize=8, loc='upper right', framealpha=0.4)

if CALIBRATION_MODE == "manual" and calib_pts:
    # 畫手動選的兩點和連線
    (x1, y1), (x2, y2) = calib_pts
    ax.plot([x1, x2], [y1, y2], 'o-',
            color='#FFD700', lw=2, ms=8, zorder=5)
    ax.annotate(f"P1\n({x1:.0f},{y1:.0f})",
                xy=(x1, y1), xytext=(x1 + 30, y1 - 60),
                color='#FFD700', fontsize=8,
                arrowprops=dict(arrowstyle='->', color='#FFD700', lw=1))
    ax.annotate(f"P2\n({x2:.0f},{y2:.0f})",
                xy=(x2, y2), xytext=(x2 + 30, y2 - 60),
                color='#FFD700', fontsize=8,
                arrowprops=dict(arrowstyle='->', color='#FFD700', lw=1))
    mid_x, mid_y = (x1 + x2) / 2, (y1 + y2) / 2
    ax.text(mid_x, mid_y - 30, f"{KNOWN_MM:.0f} mm",
            color='#FFD700', fontsize=9, ha='center',
            bbox=dict(fc='#222', ec='#FFD700', boxstyle='round,pad=0.3'))
    mode_label = f"[MANUAL] {KNOWN_MM:.0f}mm = {(np.sqrt((x2-x1)**2+(y2-y1)**2)):.0f}px"

elif CALIBRATION_MODE == "auto" and len(cm_peaks_x) >= 2:
    ax.add_patch(patches.Rectangle(
        (RULER_X1_VIS, RULER_Y1_VIS),
        1450 - RULER_X1_VIS, RULER_Y2_VIS - RULER_Y1_VIS,
        lw=1.5, ec='#FFD700', fc='#FFD700', alpha=0.15))
    for pk in cm_peaks_x:
        ax.axvline(pk, color='cyan', lw=1, ls=':', alpha=0.7)
    mode_label = f"[AUTO] {len(cm_peaks_x)} cm tick peaks"

else:
    mode_label = f"[FIXED] {PX_PER_MM:.4f} px/mm"

ax.set_title(f"Raw image + calibration markers  |  {mode_label}", fontsize=10, pad=5)
ax.axis('off')

# ─── Panel 1: 灰階 ───
ax = axes[1]
ax.imshow(gray, cmap='gray')
ax.plot(CX, CY, 'r+', ms=14, mew=2.5)
ax.set_title("Step 1 — Grayscale", fontsize=11, pad=5)
ax.axis('off')

# ─── Panel 2: 梯度圖 ───
ax = axes[2]
ax.imshow(gray, cmap='gray', alpha=0.6)
ax.imshow(grad_vis, cmap='plasma', alpha=0.6)
ax.set_xlim(CX - 250, CX + 250)
ax.set_ylim(CY + 250, CY - 250)
ax.set_title("Step 3 — Brightness gradient map", fontsize=11, pad=5)
ax.axis('off')

# ─── Panel 3: Canny + 掃描線 ───
ax = axes[3]
overlay = np.stack([gray]*3, axis=-1).copy()
overlay[edges_full > 0] = [0, 230, 220]
ax.imshow(overlay)
for (p1, p2) in line_endpoints:
    ax.plot([p1[0], p2[0]], [p1[1], p2[1]],
            color='#00ff66', lw=0.8, alpha=0.5)
ax.plot(CX, CY, 'r+', ms=14, mew=2.5)
circ = plt.Circle((CX, CY), mean_px / 2, color='red', fill=False, lw=2, ls='--')
ax.add_patch(circ)
ax.set_xlim(CX - 450, CX + 450)
ax.set_ylim(CY + 450, CY - 450)
ax.set_title(f"Step 3 — Canny edges + {len(line_endpoints)} scan lines + mean circle", fontsize=11, pad=5)
ax.axis('off')

# ─── Panel 4: 直徑直方圖 ───
ax = axes[4]
n_bins = min(20, len(diameters_mm) // 2 + 3)
ax.hist(diameters_mm, bins=n_bins, color='#00CC88', edgecolor='#007755', alpha=0.85)
ax.axvline(mean_mm,           color='#FF4444', lw=2.2, ls='-',
           label=f"Mean = {mean_mm:.3f} mm")
ax.axvline(mean_mm + std_mm,  color='#FFAA00', lw=1.8, ls='--',
           label=f"+1s = {mean_mm+std_mm:.3f} mm")
ax.axvline(mean_mm - std_mm,  color='#FFAA00', lw=1.8, ls='--',
           label=f"-1s = {mean_mm-std_mm:.3f} mm")
ax.axvline(median_mm,         color='#88AAFF', lw=1.5, ls=':',
           label=f"Median = {median_mm:.3f} mm")
ax.set_xlabel("Diameter (mm)", fontsize=10)
ax.set_ylabel("Count", fontsize=10)
ax.set_title("Step 4 — Diameter Distribution", fontsize=11, pad=5)
ax.legend(fontsize=8.5, framealpha=0.3)
ax.grid(color=GRID_CLR, lw=0.6)
ax.tick_params(colors=WHITE)

# ─── Panel 5: 各掃描線 + 統計文字 ───
ax = axes[5]

stats_txt = (
    f"Calibration: {CALIBRATION_MODE.upper()}\n"
    f"Edge method: {EDGE_METHOD}\n"
    f"Scale: {PX_PER_MM:.4f} px/mm\n"
    f"Valid lines: {len(diameters_mm)}/{N_LINES}\n"
    f"Filtered out: {n_filtered}\n"
    "─────────────────────\n"
    f"Mean:   {mean_mm:.4f} mm\n"
    f"Std:    {std_mm:.4f} mm\n"
    f"Median: {median_mm:.4f} mm\n"
    f"CV%:    {cv_pct:.1f} %\n"
    "─────────────────────\n"
    f"Min: {diameters_mm.min():.4f} mm\n"
    f"Max: {diameters_mm.max():.4f} mm"
)
ax.text(0.985, 0.98, stats_txt, transform=ax.transAxes,
        fontsize=9, va='top', ha='right', family='monospace',
        color=WHITE,
        bbox=dict(boxstyle='round,pad=0.5', fc='#1e1e1e', ec='#555', alpha=0.85))

fig.suptitle(f"Spot Size Analysis  |  Calibration: {CALIBRATION_MODE.upper()}  |  "
             f"Edge: {EDGE_METHOD}  |  Scale: {PX_PER_MM:.3f} px/mm",
             color=WHITE, fontsize=14, fontweight='bold')

fig.show()
input()
OUT_PATH = 'result.png'
fig.savefig(OUT_PATH, dpi=150, bbox_inches='tight', facecolor=DARK_BG)
plt.close(fig)
print(f"\nSaved -> {OUT_PATH}")