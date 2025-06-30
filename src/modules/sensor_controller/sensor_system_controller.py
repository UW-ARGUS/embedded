import multiprocessing as mp
from camera_transmitter.camera_device_manager import CameraDeviceManager
from imu.imu_worker import IMUWorker
from imu.imu_shared_data import IMUSharedData
import logging

class SensorSystemController:
    """
    Controls all subsystems including stop events and initialization
    """
    def __init__(self):
        self.stop_event = mp.Event()

        # Initialize imu data and setup shared memory
        self.imu_shared_array = mp.Array('d', 9)
        self.imu_data = IMUSharedData(self.imu_shared_array)

        # Create controller for subsystems
        self.camera_controller = CameraDeviceManager(
            stop_event=self.stop_event
        )
        self.imu_process = None
        self.__logger = logging.getLogger(__name__)

    def start(self):
        """ 
        Start all subsystems (IMU, camera)
        """
        self.start_imu_worker()
        self.camera_controller.start_camera_workers()

    def start_imu_worker(self):
        """
        Initializes IMU worker using shared memory
        """
        imu_worker = IMUWorker(self.stop_event, self.imu_data)
        self.imu_process = mp.Process(target=imu_worker.run, name="IMU-Worker")
        self.imu_process.start()

    def get_imu_reading(self):
        """
        Reads and returns IMU sensor data array (acc, gyro, mag) from shared memory
        """
        # print("Accel:", self.imu_data.accel)
        # print("Gyro:", self.imu_data.gyro)
        # print("Mag:", self.imu_data.mag)
        return self.imu_data.get()

    def is_running(self):
        """
        Checks and returns if all systems are still running
        """
        cam_alive = self.camera_controller.is_running()
        imu_alive = self.imu_process.is_alive() if self.imu_process else False
        return cam_alive or imu_alive

    def stop(self):
        """
        Stops all subsystem processes if event triggered
        """
        self.stop_event.set()
        
        # Stop all camera workers
        self.__logger.debug("Stopping camera workers")
        self.camera_controller.stop_workers()
        
        self.__logger.debug("Stopping IMU process")
        if self.imu_process:
            self.imu_process.join(timeout=1.0)
            if self.imu_process.is_alive():
                self.imu_process.terminate()
        
        self.__logger.debug("All processes terminated")
