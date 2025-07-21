"""
Instantiates SystemController to read IMU data, capture mutliple camera device data
Transmits over TCP socket connections
"""

import logging
import time
import sys
import os

# Add parent directory of "modules" to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules.arming_button.button import ArmingButton
from modules.device_state import DeviceState


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG, handlers=[logging.StreamHandler()]  # output to console
    )
    logging.info("Main starting")

    arming_btn = ArmingButton()

    arming_btn.update_state(DeviceState.DISARMED)
    
    # logging.info("Setting led to green")
    # arming_btn.update_state(DeviceState.ARMED)
    try:
        while True:
            time.sleep(2)
            
            # Default: DISARMED, red
            arming_btn.wait_for_press()  # Wait for button press before starting sensors
            
            # time.sleep(2)
            # logging.info("Setting led to blue") 
            input("Press Enter when ready to test again...")
            logging.info("Setting led to blue...")
            arming_btn.update_state(DeviceState.STATIONARY)
            
            
            # Read current IMU data
            # imu_reading = controller.get_imu_reading()
            # controller.imu_data.print()

            # Poll IMU to check if it reports stationary state
            # if arming_btn.state != DeviceState.STATIONARY and controller.imu_data.is_stationary():
            #     # Set colour to blue when IMU is stationary, trigger mapping
            #     arming_btn.update_state(DeviceState.STATIONARY)
            #     logging.info("Device is stationary")
            # time.sleep(1)

    except KeyboardInterrupt:
        logging.info("Process interrupted by user")
    finally:
        logging.debug("Stopping all subsystem workers")
        controller.stop()
        logging.debug("All processes stopped")
