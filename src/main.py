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

    # arming_btn.update_state(DeviceState.STATIONARY)

    # Default: DISARMED, red
    # arming_btn.wait_for_press()  # Wait for button press before starting sensors
    # # logging.info("Setting led to green")
    # arming_btn.update_state(DeviceState.ARMED)
    
    arming_btn.update_state(DeviceState.DISARMED)  # Ensure it's disarmed initially
    arming_btn.set_led_state(DeviceState.DISARMED)  # Set LED to red (disarmed)
    
     # Start the controller but don't start IMU and Camera until the button is pressed
    logging.info("Waiting for arming button press...")
    
    # Poll for button press (in background, non-blocking)
    # while arming_btn.state == DeviceState.DISARMED:
    #     arming_btn.poll_button()  # Poll the button state to detect a press
    #     time.sleep(0.05)  # Give the CPU a break to avoid overloading it with constant checks
        
    # Once the button is pressed, update the state and start subsystems
    logging.info("Arming button pressed, system armed")
    arming_btn.update_state(DeviceState.ARMED)
    
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
