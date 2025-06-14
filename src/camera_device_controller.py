import cv2
import logging
import socket

import multiprocessing as mp

from enum import Enum
from collections import deque

from camera_worker import Camera_Worker

NUM_CAMERAS = 4     # Num cameras connected to RPI
BASE_PORT = 65430   # Base port for the TCP socket transmissions
SERVER_HOST = "192.168.1.10"    # Update value with base station IP address
CAMERA_FPS = 90.0   # FPS for streaming

LOG_LEVEL = logging.INFO

class CameraDeviceMapping(Enum):
    """
    Map Camera Id based on USB Device Id
    """
    FRONT = 0
    RIGHT = 1
    LEFT = 2
    BACK = 3

class CameraDeviceController:
    """
    Controls and manages multiple Camera_Worker processes for each USB camera connected
    """
    
    def __init__(self):
        """
        Initializes Camera Device Controller which manages and handles all of the worker processes
        """
        self.worker_queue = deque() # Store active workers in queue for cleanup process
        
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s [%(processName)s] [%(levelname)s] %(message)s"
        )
        self.__logger = logging.getLogger(__name__)
        pass
    
    def start_camera_workers(self):
        """
        Start individual processes for each camera device and socket with unique port
        """
        self.__logger.info("Starting camera workers")
        
        for device_id in range(NUM_CAMERAS):
            # Create worker instance (opens camera and creates individual socket)
            self.__logger.info(f"Starting Camera_worker ({device_id}, {BASE_PORT+device_id})")
            camera_worker = self.__init_camera_worker(device_id)
            
            # Start new process and add to queue
            process = mp.Process(target=camera_worker.run_camera, name=f"Worker-{device_id}")
            process.start()
                        
            self.worker_queue.append(process)            
        
        self.__logger.info("All camera workers running")
    
    def stop_workers(self):
        """
        Stops all activate camera processes and terminates gracefully
        """
        self.__logger.info("Stopping all Camera_Worker processes")
        
        while self.worker_queue:
            process: mp.Process = self.worker_queue.popleft()
            if process.is_alive():
                self.__logger.info(f"Terminating {process.name}")
                process.terminate()
                process.join(timeout=1.0)
                
        self.__logger.info("All Camera_Worker processes terminated")
    
    def __init_camera_worker(self, device_id):
        """
        Initialize devices for all USB cameras to fetch video/ image data from
        Each Camera_Worker process controls its own docket and camera device
        """
        
        return Camera_Worker(
            host = SERVER_HOST, 
            port = BASE_PORT+device_id,
            device_id = device_id,
            fps = CAMERA_FPS
        )
        
    def is_running(self):
        """
        Check if there are any workers still alive, useful for determining if processes were terminated unexpectedly
        """
        return any(p.is_alive() for p in self.worker_queue)
        
        
    # TODO: function to check/poll if any worker process throws error. Maybe auto-restart failed workers X num of times

