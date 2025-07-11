import cv2
import logging
import os
import time

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def capture_frames_at_high_fps(
    device_id=0, save_dir="./test/2025_06_27/cf_motion2", max_frames=50, target_fps=90
):
    os.makedirs(save_dir, exist_ok=True)

    cap = cv2.VideoCapture(device_id)
    if not cap.isOpened():
        logger.error(f"Failed to open camera with ID {device_id}")
        return

    # Attempt to set FPS
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, target_fps)
    actual_fps = cap.get(cv2.CAP_PROP_FPS)
    logger.info(f"Requested FPS: {target_fps}, Actual camera FPS: {actual_fps}")

    logger.info("Capturing frames automatically at target FPS...")

    frame_count = 0
    delay = 1.0 / target_fps

    while frame_count < max_frames:
        start_time = time.time()

        ret, frame = cap.read()
        if not ret:
            logger.warning("Failed to read frame from camera")
            continue

        filename = os.path.join(save_dir, f"frame_{frame_count+1:03d}.jpg")
        cv2.imwrite(filename, frame)
        logger.info(f"Saved frame {frame_count+1} to {filename}")

        frame_count += 1

        # Delay to match target FPS
        elapsed = time.time() - start_time
        remaining = delay - elapsed
        if remaining > 0:
            time.sleep(remaining)

    cap.release()
    logger.info("Done capturing frames. Camera released.")


if __name__ == "__main__":
    capture_frames_at_high_fps()
