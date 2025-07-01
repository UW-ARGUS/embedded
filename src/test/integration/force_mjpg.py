"""
Opens specified camera and saves frames to directory with target resolution
"""
import cv2
import os
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def capture_high_fps_mjpg(device_id=0, save_dir="./test/2025_06_27/shake/test3", width=1600, height=1200, target_fps=90, max_frames=50):
    os.makedirs(save_dir, exist_ok=True)

    # MJPG capture with v4l2 backend
    cap = cv2.VideoCapture(device_id, cv2.CAP_V4L2)
    
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    cap.set(cv2.CAP_PROP_FPS, target_fps)

    actual_fps = cap.get(cv2.CAP_PROP_FPS)
    logger.info(f"Requested FPS: {target_fps}, Actual FPS: {actual_fps}")
    logger.info(f"Resolution: {cap.get(cv2.CAP_PROP_FRAME_WIDTH)}x{cap.get(cv2.CAP_PROP_FRAME_HEIGHT)}")

    if not cap.isOpened():
        logger.error("Failed to open camera.")
        return

    delay = 1.0 / target_fps
    frame_count = 0

    while frame_count < max_frames:
        start = time.time()
        ret, frame = cap.read()
        if not ret:
            logger.warning("Frame capture failed")
            continue
        fname = os.path.join(save_dir, f"frame_{frame_count:03d}.jpg")
        cv2.imwrite(fname, frame)
        logger.info(f"Saved: {fname}")
        frame_count += 1

        elapsed = time.time() - start
        remaining = delay - elapsed
        if remaining > 0:
            time.sleep(remaining)

    cap.release()
    logger.info("Done")

if __name__ == "__main__":
    capture_high_fps_mjpg()
