import multiprocessing as mp
import time
from ..camera_transmitter.camera_device_manager import CameraDeviceManager
from ..imu.imu_manager import IMUManager
from ..imu.imu_shared_data import IMUSharedData
import logging
from collections import deque

from ..device_state import DeviceState

class SystemController:
    """
    Controls all subsystems including stop events and initialization
    """

    def __init__(self):
        self.__logger = logging.getLogger(__name__)
        self.stop_event = mp.Event()

        # Initialize imu data and setup shared memory
        self.imu_shared_array = mp.Array("d", 9)
        self.imu_data = IMUSharedData(self.imu_shared_array)

        # Create controller for subsystems
        self.camera_controller = CameraDeviceManager(stop_event=self.stop_event)
        self.imu_controller = IMUManager(stop_event=self.stop_event, imu_data=self.imu_data)
        
        self.stationary_window = deque(maxlen=5) # Buffer to make sure IMU state is stationary
        # self.device_state = "MOVING"
        self.device_state = DeviceState.MOVING

        self.imu_process = None

    def start(self):
        """
        Start all subsystems (IMU, camera)
        """
        self.__logger.info("\nStarting IMU and camera workers")
        self.imu_controller.start_imu_worker(self.imu_data)
        self.camera_controller.start_camera_workers()

    # TODO: IMU should also create socket and transmit IMU readings to terminal
    def get_imu_reading(self):
        """
        Reads and returns IMU sensor data array (acc, gyro, mag) from shared memory
        """
        # see when imu starts and stops moving --> change state to stream lidar data
        return self.imu_data.get()

    def is_running(self):
        """
        Checks and returns if all systems are still running
        """
        cam_alive = self.camera_controller.is_running()
        imu_alive = self.imu_controller.is_running()
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
        self.imu_controller.stop_workers()

        self.__logger.debug("All processes terminated")

    def monitor_system_status(self):
        """
        Loop to detect if device is stationary
        """
        self.__logger.info("Monitoring system")

        try:
            while not self.stop_event.is_set():
                is_stationary = self.imu_data.is_stationary()
                self.stationary_window.append(is_stationary)

                # Checks that all entries in the specified window is stationary to confirm state change
                if all(self.stationary_window) and self.device_state != DeviceState.STATIONARY:
                    self.device_state = DeviceState.STATIONARY
                    self.__logger.info("Device STATIONARY --> triggering state change, starting mapping")

                # Checks that all entries in the specified window is moving to confirm state change
                elif not all(self.stationary_window) and self.device_state != DeviceState.MOVING:
                    self.device_state = DeviceState.MOVING
                    self.__logger.info("Motion detected --> resetting state")

                time.sleep(0.5)

        except KeyboardInterrupt:
            self.__logger.warning("System loop interrupted by user")
        finally:
            self.stop()

    def update_state_from_imu(self, is_stationary):
        if self.device_state in [DeviceState.ARMED, DeviceState.MOVING, DeviceState.STATIONARY]:
            if is_stationary and self.device_state != DeviceState.STATIONARY:
                self.set_state(DeviceState.STATIONARY)
            elif not is_stationary and self.device_state != DeviceState.MOVING:
                self.set_state(DeviceState.MOVING)
