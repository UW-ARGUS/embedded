from collections import namedtuple

class IMUSharedData:
    """
    Wraps shared memory array for IMU data. Accel, gyro, mag tuples used by systems to trigger for state changes, filtering, etc.
    """
    IMUReading = namedtuple('IMUReading', ['accel', 'gyro', 'mag'])

    def __init__(self, shared_array):
        self.shared_array = shared_array
        
    def get(self):
        """
        To safely access and read shared IMU data
        """
        with self.shared_array.get_lock():
            accel = tuple(self.shared_array[0:3])
            gyro = tuple(self.shared_array[3:6])
            mag = tuple(self.shared_array[6:9])
        return self.IMUReading(accel, gyro, mag)

    def set(self, accel, gyro, mag):
        """
        Safely set the accel, gyro, and mag IMU data values
        """
        with self.shared_array.get_lock():
            self.shared_array[0:3] = accel
            self.shared_array[3:6] = gyro
            self.shared_array[6:9] = mag
