"""
Instantiates IMUManager and IMUSharedData to capture and display imu readings
"""

import logging
import multiprocessing as mp
import time

# IMU library imports
import adafruit_icm20x
import board
import busio

import sys
import os

# Add parent directory of "modules" to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules.imu.imu_shared_data import IMUSharedData
from modules.imu.imu_manager import IMUManager

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG, handlers=[logging.StreamHandler()]  # output to console
    )
    logging.info("Starting imu test")

    try:
        stop_event = mp.Event()

        imu_shared_array = mp.Array("d", 9)
        imu_data = IMUSharedData(imu_shared_array)

        imu_manager = IMUManager(stop_event=stop_event, imu_data=imu_data)
        imu_manager.start_imu_worker(imu_data)

        while True:
            time.sleep(1)

        # while True:
        #     logging.debug("test")
        #     imu_data.print()
        #     logging.debug(f"State value: {imu_data.get_state().name}: {imu_data.get_state().value}")
        #     time.sleep(1)
    except KeyboardInterrupt:
        logging.info("Process interrupted by user")
    finally:
        logging.debug("IMU workers stopped")
        imu_data.print()
        imu_manager.stop_workers()

        


