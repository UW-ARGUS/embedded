"""
Instantiates CameraDeviceManager to capture mutliple camera device data and transmit over TCP socket connections
"""
import logging
import time
from modules.camera_transmitter.camera_device_manager import CameraDeviceManager
from embedded.src.modules.imu.imu_worker import IMUWorker
from modules.sensor_controller.sensor_system_controller import SensorSystemController

import multiprocessing as mp

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        handlers=[logging.StreamHandler()]  # output to console
    )
    logging.info("Main starting")
    
    # Starts main controller for all subsystems (IMU, Camera)
    controller = SensorSystemController()
    controller.start()

    try:
        # shared_imu_array = mp.Array('d', 9)
        # imu_data = IMUSharedData(shared_imu_array)
        # stop_event = mp.Event() # TODO: update so if this main even it stopped, camera stop event is also stopped

        # Start reading IMU data
        # imu_worker = IMUWorker(stop_event, imu_data)
        # imu_process = mp.Process(target=imu_worker.run, name="IMU-Worker")
        # imu_process.start()
        
        # Start reading camera data
        # controller = CameraDeviceManager()   
        # controller.start_camera_workers()
        
        while controller.is_running():
            # imu = controller.get_imu_reading()
            # print(f"Accel: {imu.accel}, Gyro: {imu.gyro}, Mag: {imu.mag}")
            time.sleep(1)
            
    except KeyboardInterrupt:
        logging.info("Process interrupted by user")
    finally:
        logging.debug("All workers have stopped unexpectedly!")
        controller.stop()
            
            
# init.py on source, rename to main