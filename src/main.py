"""
Instantiates SensorSystemController to read IMU data, capture mutliple camera device data, and transmit over TCP socket connections
"""
import logging
import time
from modules.sensor_controller.sensor_system_controller import SensorSystemController

import multiprocessing as mp

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        handlers=[logging.StreamHandler()]  # output to console
    )
    logging.info("Main starting")
    
    # Starts main controller for all subsystems (IMU, Camera)
    controller = SensorSystemController()
    controller.start()

    try:
        while controller.is_running():
            time.sleep(1)
            
    except KeyboardInterrupt:
        logging.info("Process interrupted by user")
    finally:
        logging.debug("All workers have stopped unexpectedly!")
        controller.stop()