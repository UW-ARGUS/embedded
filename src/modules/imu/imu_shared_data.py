import logging
import math
from collections import namedtuple
from ..device_state import DeviceState as State


class IMUSharedData:
    """
    Wraps shared memory array for IMU data.
    Accel, gyro, mag tuples used by systems to trigger for state changes, filtering, etc.
    """

    IMUReading = namedtuple("IMUReading", ["accel", "gyro", "mag"])
    # Set thresholds for stationary/ no motion detection
    ACCEL_THRESHOLD = 0.5  # Allowable noise for acceleration (m/s^2)
    GRAV_THRESHOLD = 1 # Higher threshold since stationary reading is usually around 8.5
    GYRO_THRESHOLD = 0.1  # Allowable noise for angular velocity (rads/s)
    TIME_WINDOW = 1  # Time interval to check for movement (sec)

    # Calibration values (from running calibrate_imu.py)
    # ACC_OFFSET_X, ACC_OFFSET_Y, ACC_OFFSET_Z = -0.005506663818359374, 5.941714202026368, -7.348451329467771
    # ACC_OFFSET_X, ACC_OFFSET_Y, ACC_OFFSET_Z = 0.3363853332519531, 6.556521246337891, 0.280121594238282
    # ACC_OFFSET_X, ACC_OFFSET_Y, ACC_OFFSET_Z = -0.04070142822265625, 4.015076184082031, -8.553285430908204
    ACC_OFFSET_X, ACC_OFFSET_Y, ACC_OFFSET_Z = 0,0,0
    GYRO_OFFSET_X, GYRO_OFFSET_Y, GYRO_OFFSET_Z = 0.004529862305343512, -0.010658499541984735, 0.013589586916030535
    prev_array = {
            'accel': [0.0, 0.0, 0.0],
            'gyro': [0.0, 0.0, 0.0],
            'mag': [0.0, 0.0, 0.0]
        }

    def __init__(self, shared_array):
        self.shared_array = shared_array
        self.__logger = logging.getLogger(__name__)

    def get(self):
        """
        To safely access and read shared IMU data
        """
        with self.shared_array.get_lock():
            accel = tuple(self.shared_array[0:3])
            gyro = tuple(self.shared_array[3:6])
            mag = tuple(self.shared_array[6:9])
        return self.IMUReading(accel, gyro, mag)
        
    def get_calibrated(self):
        """
        Safely access and read calibrated shared IMU data values
        """
        with self.shared_array.get_lock():
            raw_accel = self.shared_array[0:3]
            raw_gyro = self.shared_array[3:6]
            mag = self.shared_array[6:9]

        # Apply calibration offsets to accel and gyro
        calibrated_accel = (
            raw_accel[0] - self.ACC_OFFSET_X,
            raw_accel[1] - self.ACC_OFFSET_Y,
            raw_accel[2] - self.ACC_OFFSET_Z,
        )
        calibrated_gyro = (
            raw_gyro[0] - self.GYRO_OFFSET_X,
            raw_gyro[1] - self.GYRO_OFFSET_Y,
            raw_gyro[2] - self.GYRO_OFFSET_Z,
        )
        return self.IMUReading(calibrated_accel, calibrated_gyro, mag)
    
    def get_state(self):
        if self.is_stationary():
            return State.STATIONARY
        else:
            return State.MOVING

    def set(self, accel, gyro, mag):
        """
        Safely set the accel, gyro, and mag IMU data values
        """
        with self.shared_array.get_lock():
            self.shared_array[0:3] = accel
            self.shared_array[3:6] = gyro
            self.shared_array[6:9] = mag

    def print_raw(self):
        """
        Print formatted acceleration, gyro, and magnetometer values
        """
        # Note: accel Z is gravity
        # Raw values
        self.__logger.debug("Accel: X:{:.2f}, Y: {:.2f}, Z: {:.2f} m/s^2".format(*self.shared_array[0:3]))
        self.__logger.debug("Gyro: X:{:.2f}, Y: {:.2f}, Z: {:.2f} rads/s".format(*self.shared_array[3:6]))
        self.__logger.debug("Mag: X:{:.2f}, Y: {:.2f}, Z: {:.2f} uT\n".format(*self.shared_array[6:9]))

    def print(self):
        """
        Print calibrated acceleration, gyro, and magnetometer values with offsets
        """
        with self.shared_array.get_lock():
            raw_accel = self.shared_array[0:3]
            raw_gyro = self.shared_array[3:6]
            mag = self.shared_array[6:9]

        # Apply calibration offsets to accel and gyro
        calibrated_accel = (
            raw_accel[0] - self.ACC_OFFSET_X,
            raw_accel[1] - self.ACC_OFFSET_Y,
            raw_accel[2] - self.ACC_OFFSET_Z,
        )
        calibrated_gyro = (
            raw_gyro[0] - self.GYRO_OFFSET_X,
            raw_gyro[1] - self.GYRO_OFFSET_Y,
            raw_gyro[2] - self.GYRO_OFFSET_Z,
        )

        self.__logger.info(
            "Calibrated Accel: X:{:.2f}, Y: {:.2f}, Z: {:.2f} m/s^2".format(*calibrated_accel)
        )
        self.__logger.info(
            "Calibrated Gyro: X:{:.2f}, Y: {:.2f}, Z: {:.2f} rads/s".format(*calibrated_gyro)
        )
        self.__logger.info(
            "Magnetometer: X:{:.2f}, Y: {:.2f}, Z: {:.2f} uT\n".format(*mag)
        )
        
    def is_stationary(self):
        # state is based on if acceleration andd gyrometer change is within threshold
        accel_diff = [abs(c - p) for c, p in zip(self.shared_array[0:3], self.prev_array['accel'])]
        gyro_diff = [abs(c - p) for c, p in zip(self.shared_array[3:6], self.prev_array['gyro'])]

        stationary = (max(accel_diff) < self.ACCEL_THRESHOLD and
                    max(gyro_diff) < self.GYRO_THRESHOLD) 

        # Update previous with current for next check
        self.prev_array = {
            'accel': self.shared_array[0:3][:],
            'gyro': self.shared_array[3:6][:],
            'mag': self.shared_array[6:9][:]
        }
        return stationary

    def is_stationary_offset(self):
        acc_x, acc_y, acc_z = self.shared_array[0:3]
        gyro_x, gyro_y, gyro_z = self.shared_array[3:6]

        # Check if accelerometer values is close to 0 (use calibrated, offset since there may be noise)
        is_acc_zero = (
            abs((acc_x - self.ACC_OFFSET_X)) <= self.ACCEL_THRESHOLD and
            abs((acc_y - self.ACC_OFFSET_Y)) <= self.ACCEL_THRESHOLD and
            abs((acc_z - self.ACC_OFFSET_Z)) <= self.ACCEL_THRESHOLD
        )

        # Check if gyrometer values is close to 0
        is_gyro_zero = (
            abs(gyro_x-self.GYRO_OFFSET_X) <= self.GYRO_THRESHOLD and 
            abs(gyro_y - self.GYRO_OFFSET_Y) <= self.GYRO_THRESHOLD and 
            abs(gyro_z - self.GYRO_OFFSET_Z) <= self.GYRO_THRESHOLD
        )

        return is_acc_zero and is_gyro_zero


    def is_stationary_mag(self):
        """
        Check if stationary using the magnitude and so that gravity doesn't affect it
        """
        acc_x, acc_y, acc_z = self.shared_array[0:3]
        gx, gy, gz = self.shared_array[3:6]

        # Compute calibrated acceleration
        acc_x -= self.ACC_OFFSET_X
        acc_y -= self.ACC_OFFSET_Y
        acc_z -= self.ACC_OFFSET_Z

        # Compute calibrated gyroscope
        gx -= self.GYRO_OFFSET_X
        gy -= self.GYRO_OFFSET_Y
        gz -= self.GYRO_OFFSET_Z

        #  Calculate overall magnitude
        acc_mag = math.sqrt(acc_x**2 + acc_y**2 + acc_z**2)
        gyro_mag = math.sqrt(gx**2 + gy**2 + gz**2)

        is_acc_zero = abs(acc_mag) < self.ACCEL_THRESHOLD
        is_gyro_zero = gyro_mag < self.GYRO_THRESHOLD

        return is_acc_zero and is_gyro_zero