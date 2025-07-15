import logging
import multiprocessing as mp
from .imu_worker import IMUWorker


class IMUManager:
    def __init__(self, stop_event, imu_data):
        """
        Initializes IMU Manager which manages and handles the IMU worker process
        """
        # self.worker_queue = deque()  # Store active workers in queue for cleanup process
        # self.stop_event = (
        #     mp.Event()
        # )  # Shared stop event between all workers to track when should terminate

        self.stop_event = stop_event
        self.imu_data = imu_data
        self.__logger = logging.getLogger(__name__)
    def start_imu_worker(self, imu_data):
        """
        Initializes IMU worker using shared memory
        """
        self.imu_worker = IMUWorker(self.stop_event, imu_data)
        self.imu_process = mp.Process(target=self.imu_worker.run, name="IMU-Worker")
        self.imu_process.start()

    def stop_workers(self):
        """
        Stops all activate camera processes and terminates gracefully
        """
        self.__logger.info(f"Stopping IMU process {self.imu_process}")
        # Tells each worker to exit the stream_data loop
        self.stop_event.set()
        self.imu_worker.stop_imu()
        self.imu_process.terminate()
