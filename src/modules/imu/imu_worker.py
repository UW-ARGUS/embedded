import time
import logging
import board
import busio
import adafruit_icm20x


class IMUWorker:
    """
    IMU data processing for local sensing and to help change states
    """

    def __init__(self, stop_event, shared_data):
        """
        shared_data: multiprocessing Array of doubles that can hold 9 values (eg. mp.Array('d',9))
        stop_event: multiprocessing event
        """
        # IMU reading done in its own process to continuously poll sensor data without blocking camera workers
        self.stop_event = stop_event

        # Shared message queue so latest sensor readings and states are tracked and updated to trigger events
        self.shared_data = shared_data
        self.__logger = logging.getLogger(__name__)

    def run(self):
        try:
            # Intiailizie ICM 20948 IMU
            i2c = board.I2C()  # uses board.SCL and board.SDA

            self.__logger.debug("Setup i2c board clock and data")

            try:
                sensor = adafruit_icm20x.ICM20948(i2c, address=0x69)
                self.__logger.debug("IMU sensor initialized")
            except ValueError as e:
                self.__logger.error(f"No I2C device found at the given address: {e}")

            # Run until stop event triggered
            while not self.stop_event.is_set():
                # Reads accelereation, gyronometer, and magnetometer sensor data (tuple)
                accel = sensor.acceleration
                gyro = sensor.gyro
                mag = sensor.magnetic

                # Atomically update shared_data
                self.shared_data.set(accel, gyro, mag)
                # self.shared_data.print()
                # time.sleep(0.5)

                time.sleep(0.02)  # 50 Hz reading
        except Exception as e:
            self.__logger.error(f"[IMUWorker] Error: {e}")
        finally:
            self.__logger.info("IMUWorker exiting")

    def stop_imu(self):
        self.stop_event.set()

    def __del__(self):
        self.stop_imu()
