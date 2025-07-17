"""
Tests I2C connection and help calibrate IMU values for setup
"""
import os
import sys

import logging
import multiprocessing as mp
import time

# IMU library imports
import adafruit_icm20x
import board
import busio

# Add parent directory of "modules" to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules.imu.imu_shared_data import IMUSharedData
from modules.imu.imu_manager import IMUManager

# Setup I2C connection
i2c = board.I2C()  # uses board.SCL and board.SDA
logging.info("Setup i2c board clock and data")
try:
    imu = adafruit_icm20x.ICM20948(i2c, address=0x69)
    logging.debug("IMU initialized")
except ValueError as e:
    logging.error(f"No I2C device found at the given address: {e}")
    
def test_imu_connection(accel_offsets):
    while True:
        accel_x, accel_y, accel_z = imu.acceleration
        corrected_accel = apply_accel_calibration(accel_x, accel_y, accel_z, accel_offsets)

        # print the calibrarted acceleration values
        logging.info("Acceleration: X:{:.2f}, Y: {:.2f}, Z: {:.2f} m/s^2".format(*corrected_accel))
        logging.info("Gyro X:{:.2f}, Y: {:.2f}, Z: {:.2f} rads/s".format(*imu.gyro))
        logging.info("Magnetometer X:{:.2f}, Y: {:.2f}, Z: {:.2f} uT\n".format(*imu.magnetic))
        time.sleep(0.5)


def get_accel_reading_for_orientation(orientation, accel_data):
    """
    Gets accelerometer readings for different orientations and store data for offset calculations
    Prompts user to place IMU in specified orientations
    """
    logging.info(f"Place IMU in {orientation} orientation.")
    time.sleep(2)  # Wait for the device to be placed in orientation
    
    # Read accelerometer values for the current orientation
    accel_x, accel_y, accel_z = imu.acceleration
    
    # Store the accelerometer data for the current orientation
    accel_data[orientation] = (accel_x, accel_y, accel_z)
    
    # Print the accelerometer readings
    logging.info(f"Acc. readings ({orientation}): X:{accel_x}, Y:{accel_y}, Z:{accel_z}\n")


def calibrate_accelerometer():
    """
    Calibrate accelerometer by placing IMU in different orientations
    Returns calibration offsets for X, Y, Z axes
    """
    logging.info("Calibrate accelerometer by placing IMU in the following orientations")
    time.sleep(1)  # Time for user to move IMU

    # Dictionary to store accelerometer data for each orientation
    accel_data = {
        "Z+": [],
        "Z-": [],
        "X+": [],
        "X-": [],
        "Y+": [],
        "Y-": []
    }

    # Collect accelerometer readings for each orientation using the new function
    for orientation in accel_data:
        get_accel_reading_for_orientation(orientation, accel_data)
    
    # Calculate offsets for each axis
    accel_x_offset = (accel_data["X+"][0] + accel_data["X-"][0]) / 2
    accel_y_offset = (accel_data["Y+"][1] + accel_data["Y-"][1]) / 2
    accel_z_offset = (accel_data["Z+"][2] + accel_data["Z-"][2]) / 2
    
    # Print calibration offsets
    logging.info("\nFinal Accelerometer Calibration Axis Offsets:")
    logging.info(f"(X, Y, Z): {accel_x_offset}, {accel_y_offset}, {accel_z_offset}")
    
    # Return the calculated offsets
    return accel_x_offset, accel_y_offset, accel_z_offset


# Function to apply accelerometer calibration offsets
def apply_accel_calibration(accel_x, accel_y, accel_z, offsets):
    """
    Apply accelerometer calibration offsets to the raw sensor data.
    """
    accel_x_offset, accel_y_offset, accel_z_offset = offsets
    corrected_x = accel_x - accel_x_offset
    corrected_y = accel_y - accel_y_offset
    corrected_z = accel_z - accel_z_offset
    return corrected_x, corrected_y, corrected_z

# Calibrate gyroscope by checking zero-rate drift
def calibrate_gyroscope():
    time.sleep(1)  # Time for user to keep device still
    
    # Read gyroscope values when stationary
    gyro_x, gyro_y, gyro_z = imu.gyro
    
    logging.debug(f"Gyroscope readings (X, Y, Z): {gyro_x}, {gyro_y}, {gyro_z}")
    # Calibration may not be necessary for gyro since all readings are <0.1 when stationary

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG, handlers=[logging.StreamHandler()]  # output to console
    )
    logging.info("Starting imu test")

    # Call calibration functions
    accel_offsets = calibrate_accelerometer() # Calibrate accelerometer

    # Sample of applied calibration readings while using IMU
    accel_x, accel_y, accel_z = imu.acceleration
    corrected_x, corrected_y, corrected_z = apply_accel_calibration(accel_x, accel_y, accel_z, accel_offsets)
    logging.debug(f"Corrected Accel Data: X:{corrected_x}, Y:{corrected_y}, Z:{corrected_z}")

    # calibrate_accelerometer(icm)
    calibrate_gyroscope()

    # try: 
    #     test_imu_connection(accel_offsets)  # Only tests IMU connection and prints data
    # except KeyboardInterrupt:
    #     logging.info("Process interrupted by user")
    # finally:
    #     logging.debug("IMU workers stopped")

        


