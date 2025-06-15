"""
Instantiates CameraDeviceController to capture mutliple camera device data and transmit over TCP socket connections
"""
import logging
from camera_device_controller import CameraDeviceController

if __name__ == "__main__":
    logging.info("Main starting")
    controller = CameraDeviceController()
    controller.start_camera_workers()
    
    if not controller.is_running():
        print("All camera workers have stopped unexpectedly!")