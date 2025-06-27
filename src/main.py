"""
Instantiates CameraDeviceController to capture mutliple camera device data and transmit over TCP socket connections
"""
import logging
from modules.camera_transmitter.camera_device_controller import CameraDeviceController

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        handlers=[logging.StreamHandler()]  # output to console
    )
    logging.info("Main starting")

    controller = CameraDeviceController()   
    cam_map=controller.get_usb_ports()
    
    if not cam_map:
        logging.info("No cameras detected. Please connect cameras and try again.")
    else:
        for port, dev in cam_map.items():
            logging.info(f"USB port {port} -> {dev}")
    
        controller.start_camera_workers()
        
        if not controller.is_running():
            logging.debug("All camera workers have stopped unexpectedly!")
            
            
# init.py on source, rename to main