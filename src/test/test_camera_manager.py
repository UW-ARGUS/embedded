"""
Instantiates CameraDeviceController to capture mutliple camera device data and transmit over TCP socket connections
"""
import os
import sys

import logging
import multiprocessing as mp

# Add parent directory of "modules" to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules.camera_transmitter.camera_device_manager import CameraDeviceManager

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG, handlers=[logging.StreamHandler()]  # output to console
    )
    logging.info("Starting camera streaming test")

    stop_event = mp.Event()

    camera_controller = CameraDeviceManager(stop_event=stop_event)
    camera_controller.start_camera_workers()
    # camera_controller.start_camera_workers_mult_process()
