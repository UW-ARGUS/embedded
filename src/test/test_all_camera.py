"""
Tests whether each camera connected can be successfully read from
"""
import time
import cv2
import sys
import os
import logging
from pathlib import Path
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from modules.camera_transmitter.camera_device_manager import CameraDeviceManager

def main():
    current_file = Path(__file__).resolve()
    project_root = current_file.parents[2]  # Adjust depending on folder depth
    output_dir = project_root / "test" / "test_all_camera"
    manager = CameraDeviceManager(stop_event=None)

    # Get all camera usb device ports
    all_ports = manager._CameraDeviceManager__get_usb_ports()

    # Test getting one frame from each /dev/videoX path to ensure each camera can be read
    for usb_id, dev_path in all_ports.items():
        try:
            device_id = int(dev_path.replace("/dev/video", ""))  # Extract numeric ID

            logging.info(f"Opening camera {usb_id} (device_id={device_id}) at {dev_path}")
            cap = cv2.VideoCapture(device_id)

            if not cap.isOpened():
                logging.error(f"Failed to open camera at {dev_path}")
                continue

            ret, frame = cap.read()
            if ret:
                filename = os.path.join(output_dir, f"camera_{device_id}_2.jpg")
                cv2.imwrite(filename, frame)
                logging.info(f"Successfully grabbed frame from {dev_path}: shape={frame.shape}, saved to {filename}")
            else:
                logging.error(f"Failed to grab frame from {dev_path}")

            cap.release()

        except Exception as e:
            print(f"Error opening camera {usb_id}: {e}")

if __name__ == "__main__":
    main()
