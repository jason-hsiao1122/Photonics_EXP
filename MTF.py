import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from matplotlib.patches import Rectangle
from pathlib import Path
import csv

# =========================
# 1. 基本設定
# =========================

IMG_PATH = Path("MTF_50.png")

OUT_DIR = Path("mtf_output")
OUT_DIR.mkdir(exist_ok=True)

LOW_PERCENTILE = 10
HIGH_PERCENTILE = 90

# =========================
# 2. 讀圖與轉灰階
# =========================

img = mpimg.imread(IMG_PATH)

if img.ndim == 3:
    if img.shape[2] == 4:
        img = img[:, :, :3]
    gray = (
        0.299 * img[:, :, 0]
        + 0.587 * img[:, :, 1]
        + 0.114 * img[:, :, 2]
    )
else:
    gray = img.copy()

gray = gray.astype(float)

if gray.max() > 1:
    gray /= 255.0

# =========================
# 3. USAF 1951 空間頻率公式
# =========================

def usaf_frequency(group, element):
    """
    USAF 1951 spatial frequency:
    f = 2^(G + (E-1)/6) lp/mm
    """
    return 2 ** (group + (element - 1) / 6)


# =========================
# 4. 對比度量測
# =========================

def measure_contrast(gray_img, roi, orientation):
    """
    roi = (x0, y0, x1, y1)
    orientation:
        'V'：線條是垂直的，取 x 方向 profile
        'H'：線條是水平的，取 y 方向 profile
    """

    x0, y0, x1, y1 = roi
    crop = gray_img[y0:y1, x0:x1]

    if crop.size == 0:
        raise ValueError("ROI is empty. Please select a valid region.")

    if orientation.upper() == "V":
        # 垂直線條：沿 y 方向平均，得到 x 方向亮度變化
        profile = crop.mean(axis=0)

    elif orientation.upper() == "H":
        # 水平線條：沿 x 方向平均，得到 y 方向亮度變化
        profile = crop.mean(axis=1)

    else:
        raise ValueError("orientation must be 'V' or 'H'.")

    I_max = np.percentile(profile, HIGH_PERCENTILE)
    I_min = np.percentile(profile, LOW_PERCENTILE)

    contrast = (I_max - I_min) / (I_max + I_min + 1e-12)

    return contrast, I_max, I_min, profile


# =========================
# 5. Manually select all observable line groups
# =========================

records = []

fig, ax = plt.subplots(figsize=(11, 7))
ax.imshow(gray, cmap="gray", vmin=0, vmax=1)
ax.set_title("USAF image: manually select 18 ROIs")
ax.axis("on")

print("\nInstructions:")
print("You will manually select 18 vertical line-group ROIs in this order:")
print("G2E1V to G2E6V")
print("G3E1V to G3E6V")
print("G4E1V to G4E6V")
print("For each ROI, click two opposite corners of the region.\n")

for i in range(3):
    for j in range(6):

        group, element, orientation = i + 2, j + 1, "V"

        ax.set_title(
            f"Click two corners for G{group}E{element}{orientation}"
        )
        plt.draw()

        print(f"Please select ROI for G{group}E{element}{orientation}")

        pts = plt.ginput(2, timeout=0)

        if len(pts) < 2:
            print(f"G{group}E{element}{orientation}: less than two points selected, skipped.")
            continue

        x0, y0 = pts[0]
        x1, y1 = pts[1]

        x0, x1 = sorted([int(round(x0)), int(round(x1))])
        y0, y1 = sorted([int(round(y0)), int(round(y1))])

        roi = (x0, y0, x1, y1)

        try:
            contrast, I_max, I_min, profile = measure_contrast(
                gray, roi, orientation
            )
        except Exception as e:
            print(f"G{group}E{element}{orientation} measurement failed:", e)
            continue

        freq = usaf_frequency(group, element)

        record = {
            "group": group,
            "element": element,
            "orientation": orientation,
            "frequency_lp_mm": freq,
            "I_max": I_max,
            "I_min": I_min,
            "contrast": contrast,
            "x0": x0,
            "y0": y0,
            "x1": x1,
            "y1": y1,
        }

        records.append(record)

        rect = Rectangle(
            (x0, y0),
            x1 - x0,
            y1 - y0,
            fill=False,
            linewidth=1.5,
            color="r"
        )
        ax.add_patch(rect)

        ax.text(
            x0,
            y0,
            f"G{group}E{element}{orientation}",
            fontsize=8,
            bbox=dict(facecolor="white", alpha=0.6, edgecolor="none")
        )

        print(
            f"G{group} E{element} {orientation} | "
            f"f = {freq:.3f} lp/mm | "
            f"contrast = {contrast:.4f}"
        )

plt.savefig(OUT_DIR / "mtf_roi_annotated.png", dpi=300, bbox_inches="tight")
plt.show()


# =========================
# 6. 整理資料與計算 normalized MTF
# =========================

if len(records) == 0:
    raise RuntimeError("沒有量測到任何線組。")

records = sorted(records, key=lambda r: r["frequency_lp_mm"])

freqs = np.array([r["frequency_lp_mm"] for r in records])
contrasts = np.array([r["contrast"] for r in records])

# 用最低空間頻率的對比度作為 MTF 正規化基準
C0 = contrasts[0]

for r in records:
    r["MTF_norm"] = r["contrast"] / C0



# =========================
# 7. 繪製 MTF 圖
# =========================

plt.figure(figsize=(7, 5))

for orientation in ["V", "H"]:
    selected = [r for r in records if r["orientation"] == orientation]

    if len(selected) == 0:
        continue

    f = np.array([r["frequency_lp_mm"] for r in selected])
    mtf = np.array([r["MTF_norm"] for r in selected])

    idx = np.argsort(f)

    plt.plot(
        f[idx],
        mtf[idx],
        marker="o",
        linewidth=2,
        label=f"{orientation} line group"
    )

plt.xticks(np.round(np.sort(freqs), 2), rotation=45)
plt.xlabel("Spatial frequency (lp/mm)")
plt.ylabel("Normalized MTF")
plt.title("MTF from 1951 USAF Target through DCX50")
plt.grid(True, which="both", linestyle="--", alpha=0.5)
plt.legend()
plt.tight_layout()

plt.savefig(OUT_DIR / "mtf_curve.png", dpi=300)
plt.show()

print(f"MTF 圖已輸出：{OUT_DIR / 'mtf_curve.png'}")
print(f"標記 ROI 圖已輸出：{OUT_DIR / 'mtf_roi_annotated.png'}")