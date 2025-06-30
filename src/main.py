"""
Instantiates CameraDeviceManager to capture mutliple camera device data and transmit over TCP socket connections
"""
import logging
import time
from modules.camera_transmitter.camera_device_manager import CameraDeviceManager

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        handlers=[logging.StreamHandler()]  # output to console
    )
    logging.info("Main starting")

    try:
        controller = CameraDeviceManager()   
        # cam_map=controller.get_usb_ports()
        
        # if not cam_map:
        #     logging.info("No cameras detected. Please connect cameras and try again.")
        # else:
        #     for port, dev in cam_map.items():
        #         logging.info(f"USB port {port} -> {dev}")
        
        #     controller.start_camera_workers()

        #     while controller.is_running():
        #         time.sleep(1)

        controller.start_camera_workers()

        while controller.is_running():
            time.sleep(1)
            
            # if not controller.is_running():
    except KeyboardInterrupt:
        logging.info("Process interrupted by user")
    finally:
            logging.debug("All camera workers have stopped unexpectedly!")
            controller.stop_workers()
            
            
# init.py on source, rename to main