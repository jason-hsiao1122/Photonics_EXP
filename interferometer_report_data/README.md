# 干涉儀結報資料與程式

本資料夾包含本次實驗的 29 張原始影像、重現可視度取樣與擬合的 Python 程式，以及 BK7 玻璃片光程差表程式。影像資料為原始檔；執行程式會在 outputs 產生另存的紅框圖，並不覆寫 images。

## 使用方式

在此資料夾執行 `python -m pip install -r requirements.txt`，然後依序執行：

1. `python analyze_visibility.py`：根據程式列出的單一取樣範圍，取中央九列平均，對框內剖面以標準差 6 像素的高斯函數平滑，再以最大、最小值計算 V；輸出標記影像、values.csv 及數據圖。
2. `python fit_visibility.py`：讀取 outputs/values.csv，將零位移可視度固定，以未加權最小平方擬合指數衰減曲線，圖中標出 V₀/e。位移 d 為鏡面相對位移，擬合採 ΔOPD = 2|d|，Lc 定義為包絡降至 V₀/e 的相對光程差。
3. `python bk7_table.py`：使用 SCHOTT N-BK7 Sellmeier 係數、532 nm 波長與 1 mm 厚度計算題目 1 的表格。

綠光所有測點高於 V₀/e，估計同調長度依賴外推，且部分資料不單調與影像亮部截斷，結果不可靠。紅光遠離零點時條紋很弱，估計亦僅供粗略比較。影像非經校正的光強，取樣區域經人工選定；標記影像不應視為新的量測。

`outputs/values.csv` 包含取樣範圍與計算結果，影像路徑相對於本資料夾。波長、距離和未記錄的條件以結報及數據索引為準。

## 資料來源

- 原始實驗影像：本組紀錄。
- 干涉儀講義：DOC. 214，2026 年版。
- SCHOTT N-BK7 色散係數：https://media.schott.com/api/public/content/41e799d0bf874807a0bb8e702fbb75b5?v=54856406

