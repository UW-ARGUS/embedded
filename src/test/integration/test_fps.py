"""
Test whether fps is set correctly (what was attempted to be set and actual)
"""

import cv2
import time

# cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
cap = cv2.VideoCapture("/dev/video0", cv2.CAP_V4L2)
cap.set(cv2.CAP_PROP_FPS, 90)

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

print("FPS set:", cap.get(cv2.CAP_PROP_FPS))

t0 = time.time()
frames = 0
while frames < 90:
    ret, frame = cap.read()
    if ret:
        frames += 1
t1 = time.time()

print(f"Captured {frames} frames in {t1 - t0:.2f} seconds ? Actual FPS: {frames / (t1 - t0):.2f}")
cap.release()
