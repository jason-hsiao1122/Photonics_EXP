import cv2
import numpy as np
import sys

points = []
MAX_W, MAX_H = 1280, 800

def pixel_dist(p1, p2):
    return np.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)

path = 'DCV_5.jpg'
img = cv2.imread(path)
if img is None:
    print("Cannot open image."); sys.exit(1)

h, w = img.shape[:2]
scale_display = min(MAX_W / w, MAX_H / h, 1.0)
display = cv2.resize(img, (int(w * scale_display), int(h * scale_display)))

def click(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        points.append((int(x / scale_display), int(y / scale_display)))
        if len(points) == 2:
            print("Calibration done. Click point 3 to start measuring...")
        elif len(points) == 3:
            print("Click point 4...")
        cv2.imshow("Measure", display)

cv2.imshow("Measure", display)
cv2.setMouseCallback("Measure", click)
print("Click 2 calibration points (1 cm apart), then 2 measurement points...")

while len(points) < 4:
    cv2.waitKey(10)

cv2.destroyAllWindows()

# Compute distances
scale_cm = pixel_dist(points[0], points[1])
dist_cm = pixel_dist(points[2], points[3]) / scale_cm

# Draw on original image
out = img.copy()
GREEN, RED = (0, 200, 0), (0, 0, 255)
FONT = cv2.FONT_HERSHEY_SIMPLEX

# Calibration: green line, green dots, "1.00 cm" label
cv2.line(out, points[0], points[1], GREEN, 2)
for p in points[:2]:
    cv2.circle(out, p, 6, GREEN, -1)
mid_cal = ((points[0][0]+points[1][0])//2, (points[0][1]+points[1][1])//2)
cv2.putText(out, "1.00 cm", (mid_cal[0]+8, mid_cal[1]-8), FONT, 1.2, GREEN, 2)

# Measurement: red line, red dots, distance label
cv2.line(out, points[2], points[3], RED, 2)
for p in points[2:]:
    cv2.circle(out, p, 6, RED, -1)
mid_meas = ((points[2][0]+points[3][0])//2, (points[2][1]+points[3][1])//2)
cv2.putText(out, f"{dist_cm:.2f} cm", (mid_meas[0]+8, mid_meas[1]-8), FONT, 1.2, RED, 2)

out_path = path[:-4] + '_result.jpg'
cv2.imwrite(out_path, out)
print(f"\nCalibration: {scale_cm:.1f} px = 1 cm")
print(f"Distance: {dist_cm:.2f} cm")
print(f"Saved: {out_path}")