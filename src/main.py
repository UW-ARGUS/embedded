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

    arming_btn = ArmingButton()  # Default: DISARMED, red

    # Starts main controller for all subsystems (IMU, Camera)
    controller = SystemController()
    
     # Initialize the controller but don't start IMU and Camera until the button is pressed
    arming_btn.wait_for_press_2() # Wait for button press before starting sensors
            
    # Once the button is pressed, update the state and start subsystems
    controller.start()  # Start camera and IMU workers
    prev_state = arming_btn.state
    try:
        while controller.is_running():
            # Read current IMU data
            # imu_reading = controller.get_imu_reading()
            # controller.imu_data.print()
            
            current_state = controller.imu_data.get_state()
            
            # Poll IMU state and update button state accordingly if changed, display state colour on button LED
            if current_state != prev_state:
                arming_btn.update_state(current_state)
                logging.info(f"State updated: {current_state}, {controller.imu_data.is_stationary()}")
                prev_state = current_state

            time.sleep(0.5)

    except KeyboardInterrupt:
        logging.info("Process interrupted by user")
    finally:
        logging.debug("Stopping all subsystem workers")
        controller.stop()
        logging.debug("All processes stopped")
