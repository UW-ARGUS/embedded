"""
Instantiates CameraDeviceController to capture mutliple camera device data and transmit over TCP socket connections
"""

import logging
# import multiprocessing as mp
# from ...modules.imu.imu_shared_data import IMUSharedData
# from ...modules.imu.imu_manager import IMUManager
import time

import board
import busio

import adafruit_icm20x


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG, handlers=[logging.StreamHandler()]  # output to console
    )
    logging.info("Starting imu test")

    # stop_event = mp.Event()

    # imu_shared_array = mp.Array("d", 9)
    # imu_data = IMUSharedData(imu_shared_array)

    # imu_manager = IMUManager(stop_event=stop_event, imu_data=imu_data)

    i2c = board.I2C()  # uses board.SCL and board.SDA
    # i2c = busio.I2C(board.SCL, board.SDA, frequency=400000)

    logging.info("Setup i2c board clock and data")
    time.sleep(1)

    # icm = adafruit_icm20x.ICM20948(i2c, address=0x69)

    try:
        icm = adafruit_icm20x.ICM20948(i2c, address=0x69)
        logging.debug("IMU initialized")
    except ValueError as e:
        logging.error(f"No I2C device found at the given address: {e}")

    # i2c = board.STEMMA_I2C()  # For using the built-in STEMMA QT connector on a microcontroller

    while True:
        logging.info("Acceleration: X:{:.2f}, Y: {:.2f}, Z: {:.2f} m/s^2".format(*icm.acceleration))
        logging.info("Gyro X:{:.2f}, Y: {:.2f}, Z: {:.2f} rads/s".format(*icm.gyro))
        logging.info("Magnetometer X:{:.2f}, Y: {:.2f}, Z: {:.2f} uT".format(*icm.magnetic))
        logging.info("")
        time.sleep(0.5)

    # cam_map = imu_manager.get_usb_ports()

    # if not cam_map:
    #     logging.info("No cameras detected. Please connect cameras and try again.")
    # else:
    #     # for port, dev in cam_map.items():
    #     #     logging.info(f"USB port {port} -> {dev}")

    #     imu_manager.start_imu_worker()

    #     if not imu_manager.is_running():
    #         logging.debug("All camera workers have stopped unexpectedly!")
