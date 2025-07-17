"""
Instantiates SystemController to read IMU data, capture mutliple camera device data
Transmits over TCP socket connections
"""

import logging
import time
from modules.system_controller.system_controller import SystemController
from modules.arming_button.button import ArmingButton
from modules.device_state import DeviceState

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG, handlers=[logging.StreamHandler()]  # output to console
    )
    logging.info("Main starting")

    arming_btn = ArmingButton()

    # Starts main controller for all subsystems (IMU, Camera)
    controller = SystemController()

    # Default: DISARMED, red
    arming_btn.wait_for_press()  # Wait for button press before starting sensors
    controller.start()  # Start camera and IMU workers

    try:
        while controller.is_running():
            # Read current IMU data
            # imu_reading = controller.get_imu_reading()
            # controller.imu_data.print()

            # Poll IMU to check if it reports stationary state
            if arming_btn.state != DeviceState.STATIONARY and controller.imu_data.is_stationary():
                # Set colour to blue when IMU is stationary, trigger mapping
                arming_btn.update_state(DeviceState.STATIONARY)
                logging.info("Device is stationary")
            time.sleep(1)

    except KeyboardInterrupt:
        logging.info("Process interrupted by user")
    finally:
        logging.debug("Stopping all subsystem workers")
        controller.stop()
        logging.debug("All processes stopped")
