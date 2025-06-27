import cv2
import logging
import socket

import subprocess
import re

import multiprocessing as mp

from enum import Enum
from collections import deque

from .camera_worker import CameraWorker

# TODO: Move constants to .yaml file
NUM_CAMERAS = 4     # Num cameras connected to RPI
BASE_PORT = 65430   # Base port for the TCP socket transmissions
SERVER_HOST = "192.168.1.10"    # Update value with base station IP address
CAMERA_FPS = 90.0   # FPS for streaming

LOG_LEVEL = logging.DEBUG

class CameraDeviceController:
    """
    Controls and manages multiple Camera_Worker processes for each USB camera connected
    """
    def __init__(self):
        """
        Initializes Camera Device Controller which manages and handles all of the worker processes
        """
        self.worker_queue = deque() # Store active workers in queue for cleanup process
        self.stop_event = mp.Event() # Shared stop event between all workers to track when should terminate
        
        logging.basicConfig(
            level=LOG_LEVEL,
            handlers=[logging.StreamHandler()]  # output to console
        )
        self.__logger = logging.getLogger(__name__)

    def get_usb_ports(self):
        """
        Use `v4l2-ctl --list-devices` to find USB cameras and map USB port numbers to /dev/video devices.
        If no cameras are connected or if the command fails, logs a warning and returns an empty dict.
        """
        logging.info("Scanning USB camera devices with v4l2-ctl...")

        try:
            result = subprocess.run(
                ['v4l2-ctl', '--list-devices'],
                capture_output=True,
                text=True,
                check=True
            )
        except FileNotFoundError:
            logging.error("v4l2-ctl command not found. Please install v4l-utils.")
            return {}
        except subprocess.CalledProcessError as e:
            # This error can occur if no devices are found, so handle gracefully
            logging.warning("No USB cameras detected or unable to list devices.")
            logging.debug(f"v4l2-ctl output: {e.output}")
            return {}

        output = result.stdout
        camera_map = {}
        current_port = None

        for line in output.splitlines():
            # Look for lines containing USB port identifiers, e.g., usb-0000:01:00.0-1.3
            match = re.search(r'usb-\S+-(\d+(\.\d+)*)', line)
            if match:
                current_port = match.group(1)  # e.g., '1.3'
            elif '/dev/video' in line and current_port is not None:
                video_dev = line.strip()
                camera_map[current_port] = video_dev
                current_port = None

        if not camera_map:
            logging.warning("No USB cameras found.")
        else:
            logging.info(f"Detected {len(camera_map)} USB camera(s): {camera_map}")
        
        self.camera_map = camera_map

        return camera_map

    def start_camera_workers(self):
        """
        Start individual processes for each camera device and socket with unique port
        """
        self.__logger.info("Starting camera workers")
        
        cam_map = self.get_usb_ports()
        for port, dev in cam_map.items():
            self.__logger.info(f"USB port {port} -> {dev}")
        
        # TODO: Manually get the USB device port numbers (maybe using lsusb) and only start the cameras that are actually connected
        for device_id in range(NUM_CAMERAS):
            # Create worker instance (opens camera and creates individual socket)
            self.__logger.info(f"Starting Camera_worker ({device_id}, {BASE_PORT+device_id})")
            
            # Initialize devices for all USB cameras to fetch video/ image data from. Each Camera_Worker process controls its own socket and camera device
            camera_worker = CameraWorker(
                host = SERVER_HOST, 
                port = BASE_PORT+device_id,
                device_id = device_id,
                fps = CAMERA_FPS,
                stop_event = self.stop_event
            )
            
            # Start new process and add to queue
            process = mp.Process(target=camera_worker.run_camera, name=f"Worker-{device_id}")
            process.start()
                        
            self.worker_queue.append(process)            
        
        self.__logger.info("All camera workers running")
    
    def __stop_workers(self):
        """
        Stops all activate camera processes and terminates gracefully
        """
        self.__logger.info("Stopping all Camera_Worker processes")
        # Tells each worker to exit the stream_data loop
        self.stop_event.set()
        
        for worker in self.worker_queue:
            worker.join()
        self.__logger.info("All workers stopped")
        
        while self.worker_queue:
            process: mp.Process = self.worker_queue.popleft()
            if process.is_alive():
                self.__logger.info(f"Terminating {process.name}")
                process.terminate()
                # process.join(timeout=1.0)
                
        self.__logger.info("All Camera_Worker processes terminated")
    
    def __init_camera_worker(self, device_id, stop_event):
        """
        
        """
        return CameraWorker(
            host = SERVER_HOST, 
            port = BASE_PORT+device_id,
            device_id = device_id,
            fps = CAMERA_FPS,
            stop_event = self.stop_event
        )
        
    def is_running(self):
        """
        Check if there are any workers still alive, useful for determining if processes were terminated unexpectedly
        """
        return any(p.is_alive() for p in self.worker_queue)
        
        
    # TODO: function to check/poll if any worker process throws error. Maybe auto-restart failed workers X num of times



