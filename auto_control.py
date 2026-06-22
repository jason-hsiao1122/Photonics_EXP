import matplotlib.pyplot as plt
import serial
import time
import numpy as np
from scipy.optimize import curve_fit
from scipy.stats import norm


arduino = serial.Serial(port='COM13', baudrate=115200, timeout =.1) # arduino


s = serial.Serial("COM10", 9600, timeout=5) # Powermeter

x_position =[]
y_position =[]

step_time = 0.004
ten_steps_dis = 1.70 # 步進馬達 10 steps 距離，單位 mm

def get_data():
    for i in range(200):

        arduino.write(bytes("3", "utf-8"))
        s.write(("*CAU\n").encode())
        response = s.readline().decode().strip()
        arduino.write(bytes("1", "utf-8"))
        time.sleep(step_time)

        x_position.append(i * ten_steps_dis / 10) # Unit: mm
        y_position.append(float(response))  
        print(i,"儀器回應:",float(response))

    arduino.write(bytes("3", "utf-8"))

    return x_position, y_position

def get_test_data():

    # 400 個位置點，從左掃到右
    x_position = np.linspace(0, 10, 400)

    # CDF 參數
    x0 = 5.0        # CDF 中心位置
    sigma = 0.7    # 標準差，控制曲線寬度
    low = 0      # Low intensity
    high = 3.20     # High intensity

    # 使用 normal CDF，不使用 erf
    y_clean = low + (high - low) * norm.cdf(
        x_position,
        loc=x0,
        scale=sigma
    )

    # 加入量測雜訊，不設定 random seed
    noise = np.random.normal(0, 0.15, size=len(x_position))
    y_position = y_clean + noise

    # 限制範圍
    y_position = np.clip(y_position, low, high)

    # 確保 CDF 單調遞增
    y_position = np.maximum.accumulate(y_position)
    y_position[0:100] = y_position[100]

    return x_position, y_position

x_position, y_position = get_data()
# x_position, y_position = get_test_data()

x = np.array(x_position, dtype=float)
y = np.array(y_position, dtype=float)

# 排序
idx = np.argsort(x)
x = x[idx]
y = y[idx]

# 將 CDF 正規化到 0~1
y_norm = y - y.min()
y_norm = y_norm / y_norm.max()

# CDF 擬合函數：error function 型態
def cdf_fit(x, A, mu, sigma, C):
    from scipy.special import erf
    return C + A * 0.5 * (1 + erf((x - mu) / (np.sqrt(2) * sigma)))

A0 = y.max() - y.min()
mu0 = x[np.argmin(np.abs(y_norm - 0.5))]
sigma0 = (x.max() - x.min()) / 6
C0 = y.min()

popt, pcov = curve_fit(
    cdf_fit, x, y,
    p0=[A0, mu0, sigma0, C0],
    maxfev=10000
)

A, mu, sigma, C = popt
sigma = abs(sigma)

x_fit = np.linspace(x.min(), x.max(), 2000)
y_fit = cdf_fit(x_fit, A, mu, sigma, C)

# 用原始 y 的 high / low 定義 10%、90%
low_intensity = y.min()
high_intensity = y.max()

I10 = low_intensity + 0.10 * (high_intensity - low_intensity)
I90 = low_intensity + 0.90 * (high_intensity - low_intensity)

# 用原始資料找最接近 10%、90% 的點
idx10 = np.argmin(np.abs(y - I10))
idx90 = np.argmin(np.abs(y - I90))

x10 = x[idx10]
y10 = y[idx10]

x90 = x[idx90]
y90 = y[idx90]

d_10_90 = abs(x90 - x10)
beam_width = 0.78 * d_10_90

print(f"Low intensity  = {low_intensity:.6g}")
print(f"High intensity = {high_intensity:.6g}")
print(f"10% intensity  = {I10:.6g}")
print(f"90% intensity  = {I90:.6g}")

print(f"\n10% position:")
print(f"x10 = {x10:.6g}, y10 = {y10:.6g}")

print(f"\n90% position:")
print(f"x90 = {x90:.6g}, y90 = {y90:.6g}")

print(f"\nd_10%~90% = {d_10_90:.6g}")
print(f"Beam width = 0.78 * d_10%~90% = {beam_width:.6g}")

plt.figure(figsize=(9, 5))

plt.scatter(x, y, s=20, label="Raw CDF data")
plt.plot(x_fit, y_fit, label="CDF fit", color = 'r')

plt.scatter(x10, y10, s=100, marker="o", label="10% point")
plt.scatter(x90, y90, s=100, marker="s", label="90% point")

plt.axhline(low_intensity, linestyle="-.", label="Low intensity")
plt.axhline(high_intensity, linestyle="-.", label="High intensity")


plt.text(x10, y10, f" 10%\nx={x10:.3g}")
plt.text(x90, y90, f" 90%\nx={x90:.3g}")

plt.xlabel("Position(mm)")
plt.ylabel("Intensity(mW)")
plt.title(f"Beam Width = {beam_width:.4g} mm")
plt.legend()
plt.grid(True)
plt.show()