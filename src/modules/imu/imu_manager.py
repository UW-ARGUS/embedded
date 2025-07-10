import multiprocessing as mp
from imu_worker import IMUWorker

class IMUManager:
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