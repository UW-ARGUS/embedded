"""
Instantiates SystemController to read IMU data, capture mutliple camera device data
Transmits over TCP socket connections
"""

import logging
import time
from modules.system_controller.system_controller import SystemController

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG, handlers=[logging.StreamHandler()]  # output to console
    )
    logging.info("Main starting")

    # Starts main controller for all subsystems (IMU, Camera)
    controller = SystemController()
    controller.start()

    try:
        while controller.is_running():
            # Read current IMU data
            # imu_reading = controller.get_imu_reading()
            controller.imu_data.print()

            # Poll IMU to check if it reports stationary state
            stationary = controller.imu_data.is_stationary()

            if stationary:
                logging.info("IMU is stationary")
                # TODO: Trigger mapping or change button colour
            else:
                logging.info("IMU is moving")
            time.sleep(1)

    except KeyboardInterrupt:
        logging.info("Process interrupted by user")
    finally:
        logging.debug("Stopping all subsystem workers")
        controller.stop()
        logging.debug("All processes stopped")
