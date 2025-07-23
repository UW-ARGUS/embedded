import time
import logging

import subprocess
import re

import multiprocessing as mp

from collections import deque
from dataclasses import dataclass

from .camera_worker import CameraWorker

# TODO: Move constants to .yaml file
NUM_CAMERAS = 4  # Num cameras connected to RPI
BASE_PORT = 5000  # Base port for the TCP socket transmissions
SERVER_HOST = "127.0.0.1"
# SERVER_HOST = "192.168.194.44" # "192.168.194.241"
# SERVER_HOST= "192.168.194.24" # florence laptop2
# Mihir: "192.168.194.44" # "192.168.68.172"# Florence "192.168.194.189"# "192.168.194.44" # "192.168.194.77" # "192.168.2.208"  #  "192.168.194.189"  #"192.168.194.44" #   # Update value with base station IP address
# CAMERA_FPS = 90.0  # FPS for streaming
CAMERA_FPS = 2.0
# SERVER_HOST = "127.0.0.1" # pi
LOG_LEVEL = logging.DEBUG

@dataclass
class CameraWorkerInfo:
    """
    Worker queue info
    """
    process: mp.Process
    device_id: int
    port: int

@dataclass
class CameraInfo:
    device_id: int
    port: int
    camera_worker: CameraWorker


class CameraDeviceManager:
    USB_REGEX = r"\((usb-[^)]+)\)"
    """
    Controls and manages multiple Camera_Worker processes for each USB camera connected
    """

    def __init__(self, stop_event):
        """
        Initializes Camera Device Controller which manages and handles all of the worker processes
        """
        self.worker_queue = deque()  # Store active workers in queue for cleanup process
        self.stop_event = (
            mp.Event()
        )  # Shared stop event between all workers to track when should terminate

        # self.stop_event = stop_event
        self.__logger = logging.getLogger(__name__)
        self.camera_map = {}  # List of usb camera devices connected
        
        self.camera_queue = deque()

    def __get_usb_ports(self):
        """
        Uses `v4l2-ctl --list-devices` to find USB cameras
        Map USB port numbers to /dev/video devices.
        If no cameras are connected or if the command fails, logs warning and returns an empty dict.
        """
        logging.info("Scanning USB camera devices with v4l2-ctl...")

        try:
            result = subprocess.run(
                ["v4l2-ctl", "--list-devices"], capture_output=True, text=True, check=True
            )
        except FileNotFoundError:
            logging.error("v4l2-ctl command not found. Please install v4l-utils.")
            return None
        except subprocess.CalledProcessError as e:
            # This error can occur if no devices are found, so handle gracefully
            logging.warning("No USB cameras detected or unable to list devices.")
            # logging.debug(f"v4l2-ctl output: {e.output}")
            return {}

        output = result.stdout
        camera_map = {}
        current_port = None
        current_devices = []
        # logging.debug(f"v4l2 output: {output}")

        for line in output.splitlines():
            # Skip empty lines
            if not line.strip():
                continue

            # New device block
            match = re.search(self.USB_REGEX, line)
            if match:
                # If we have a previous camera, save the first video device
                if current_port and current_devices:
                    video_dev = next((dev for dev in current_devices if "/dev/video" in dev), None)
                    if video_dev:
                        camera_map[current_port] = video_dev

                # Start new block
                current_port = match.group(1)  # e.g., '1' or '1.3'
                current_devices = []
            elif line.strip().startswith("/dev/video"):
                current_devices.append(line.strip())

        # Catch the last block
        if current_port and current_devices:
            video_dev = next((dev for dev in current_devices if "/dev/video" in dev), None)
            if video_dev:
                camera_map[current_port] = video_dev

        if not camera_map:
            logging.warning("No USB cameras found.")
        else:
            logging.info(f"Detected {len(camera_map)} USB camera(s): {camera_map}")

        self.camera_map = camera_map

        return camera_map
    
    def start_camera_workers_mult_process(self, cam_map=None):
        """
        Start individual processes for each camera device and socket with unique port
        """
        self.__logger.info("Starting camera workers")

        if cam_map == None:
            cam_map = self.__get_usb_ports()
        # for port, dev in cam_map.items():
        #     self.__logger.info(f"USB port {port} -> {dev}")

        # Manually get USB device port numbers, only starting cameras actually connected
        for i, port in enumerate(cam_map.items()):
            # device_idx = int(port[0])
            device_path = port[1]
            device_id = int(device_path.replace("/dev/video", ""))  # Extract device id
            # self.__logger.info(f"device_id: {device_id}, {i},{len(cam_map)}")

            device_port = BASE_PORT + i
            # self.__logger.info(f"USB port {port} -> {device_path}")

            # Create worker instance (opens camera and creates individual socket)
            self.__logger.info(
                f"Starting Camera_worker ({device_id}, {device_port})"
            )  # Port is incremented by 1 each time in cam_map

            # Initialize devices for all USB cameras to fetch video/ image data from
            # Each CameraWorker process controls its own socket and camera device
            camera_worker = CameraWorker(
                host=SERVER_HOST,
                port=device_port,
                device_id=device_id,
                fps=CAMERA_FPS,
                stop_event=self.stop_event,
            )

            # Start new process and add to queue
            process = mp.Process(target=camera_worker.run_camera, name=f"Worker-{device_id}")
            process.start()

            self.worker_queue.append(CameraWorkerInfo(
                    process=process,
                    device_id=device_id,
                    port=device_port,
                )
            )

        self.__logger.info(f"All camera workers running {[w.process.name for w in self.worker_queue]}\n")


    def start_camera_workers(self, cam_map=None, limit=None):
        """
        Start individual processes for each camera device and socket with unique port
        """
        self.__logger.info("Starting camera workers")

        if cam_map == None:
            cam_map = self.__get_usb_ports()
        
        # Limit how many cameras to start
        items = list(cam_map.items())
        if limit is not None:
            items = items[:limit]

        # Manually get USB device port numbers, only starting cameras actually connected
        for i, port in enumerate(cam_map.items()):
            device_path = port[1]
            device_id = int(device_path.replace("/dev/video", ""))  # Extract device id

            device_port = BASE_PORT + i

            # Create worker instance (opens camera and creates individual socket)
            self.__logger.info(
                f"Starting Camera_worker ({device_id}, {device_port})"
            )  # Port is incremented by 1 each time in cam_map

            # Initialize devices for all USB cameras to fetch video/ image data from
            # Each CameraWorker process controls its own socket and camera device
            camera_worker = CameraWorker(
                host=SERVER_HOST,
                port=device_port,
                device_id=device_id,
                fps=CAMERA_FPS,
                stop_event=self.stop_event,
            )
            
            # Setup camera
            camera_worker.run_camera()
            
            self.camera_queue.append(CameraInfo(
                    device_id=device_id,
                    port=device_port,
                    camera_worker=camera_worker,
                )
            )

            # Start new process and add to queue
            # process = mp.Process(target=camera_worker.run_camera, name=f"Worker-{device_id}")
            # process.start()

            # self.worker_queue.append(CameraWorkerInfo(
            #         process=process,
            #         device_id=device_id,
            #         port=device_port,
            #     )
            # )
            
        # Start new process and add to queue
        process = mp.Process(target=self.run_workers) #, name=f"Worker-{device_id}")
        process.start()

        self.worker_queue.append(CameraWorkerInfo(
                process=process,
                device_id=device_id,
                port=device_port,
            )
        )
        self.__logger.info(f"All camera workers running {[w.device_id for w in self.camera_queue]}\n")

        # self.__logger.info(f"All camera workers running {[w.process.name for w in self.worker_queue]}\n")
    def run_workers(self):
        # poll cameras
        while not self.stop_event.is_set():
            self.__logger.info(f"Running cameras")
            for worker in self.camera_queue:
                try:
                    self.__logger.info(f"Streaming camera {worker.device_id}")
                    worker.camera_worker.stream_single_frame()
                except Exception as e:
                    self.__logger.info(f"error: {e}")
                time.sleep(0.5)

    def stop_workers(self):
        """
        Stops all activate camera processes and terminates gracefully
        """
        self.__logger.info(f"Stopping all Camera_Worker processes {self.worker_queue}")
        # Tells each worker to exit the stream_data loop
        self.stop_event.set()

         # Try to join all processes
        for worker in self.worker_queue:
            if worker.process.is_alive():
                worker.process.join() # TODO: See if need timeout=5.0

        self.__logger.info("All workers joined")

        # Force terminate and cleanup any remaining alive workers
        for worker in self.worker_queue:
            if worker.process.is_alive():
                self.__logger.warning(f"Terminating Camera_Worker {worker['device_id']}")
                worker.process.terminate()
                # worker.process.join(timeout=1.0)

        self.worker_queue.clear()
        self.__logger.info("All Camera_Worker processes terminated")

    def is_running(self):
        """
        Check if there are any workers still alive
        Useful for determining if processes were terminated unexpectedly
        """
        return any(worker.process.is_alive() for worker in self.worker_queue)


    # TODO: function to check/poll if any worker process throws error
    # Maybe auto-restart failed workers X num of times
    def monitor_workers(self):
        """
        Monitors and auto-restarts worker mapping to device id if they crash
        """
        while not self.stop_event.is_set():
            for i, worker_info in enumerate(self.worker_queue):
                process = worker_info.process
                device_id = worker_info.device_id

                # Process crashed, create new worker and restart process
                if not process.is_alive():
                    worker_info = self.worker_queue[i]
                    self.__logger.warning(f"Worker {process.name} crashed. Restarting...")

                    new_worker = CameraWorker(
                        host=self.SERVER_HOST,
                        port=worker_info.port,
                        device_id=device_id,
                        fps=self.CAMERA_FPS,
                        stop_event=self.stop_event,
                    )

                    # Start the new process
                    new_process = mp.Process(
                        target=new_worker.run_camera, name=f"Worker-{device_id}"
                    )
                    new_process.start()

                    # Update the worker information to include new process
                    worker_info.process=new_process
            time.sleep(1)
