"""
Instantiates CameraDeviceController to capture mutliple camera device data and transmit over TCP socket connections
"""

import logging
from modules.camera_transmitter.camera_device_manager import CameraDeviceManager
import multiprocessing as mp

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG, handlers=[logging.StreamHandler()]  # output to console
    )
    logging.info("Starting camera streaming test")

    stop_event = mp.Event()

    camera_controller = CameraDeviceManager(stop_event=stop_event)
    camera_controller.start_camera_workers()
