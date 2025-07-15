import time
import logging

import subprocess
import re

import multiprocessing as mp

from collections import deque

from .camera_worker import CameraWorker

# TODO: Move constants to .yaml file
NUM_CAMERAS = 4  # Num cameras connected to RPI
BASE_PORT = 5000  # Base port for the TCP socket transmissions
SERVER_HOST = "192.168.194.44" # "192.168.194.189"  # Update value with base station IP address
CAMERA_FPS = 90.0  # FPS for streaming

LOG_LEVEL = logging.DEBUG


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
            logging.debug(f"v4l2-ctl output: {e.output}")
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

    def start_camera_workers(self):
        """
        Start individual processes for each camera device and socket with unique port
        """
        self.__logger.info("Starting camera workers")

        cam_map = self.__get_usb_ports()
        for port, dev in cam_map.items():
            self.__logger.info(f"USB port {port} -> {dev}")

        # Manually get USB device port numbers, only starting cameras actually connected
        for i, port in enumerate(cam_map.items()):
            # device_idx = int(port[0])
            device_path = port[1]
            device_id = int(device_path.replace("/dev/video", ""))  # Extract device id
            self.__logger.info(f"device_id: {device_id}, {i},{len(cam_map)}")

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

            # Start new process and add to queue
            process = mp.Process(target=camera_worker.run_camera, name=f"Worker-{device_id}")
            process.start()

            self.worker_queue.append(
                {
                    "process": process,
                    "device_id": device_id,
                    "port": device_port,
                }
            )

        self.__logger.info(f"All camera workers running {self.worker_queue}")

    def stop_workers(self):
        """
        Stops all activate camera processes and terminates gracefully
        """
        self.__logger.info(f"Stopping all Camera_Worker processes {self.worker_queue}")
        # Tells each worker to exit the stream_data loop
        self.stop_event.set()

        for worker in self.worker_queue:
            worker.join()
        self.__logger.info("All workers stopped")

        while self.worker_queue:
            process: mp.Process = self.worker_queue.popleft()
            self.__logger.info(f"process: {process.is_alive()}")
            if process.is_alive():
                self.__logger.info(f"Terminating {process.name}")
                process.terminate()
                # process.join(timeout=1.0)

        self.__logger.info("All Camera_Worker processes terminated")

    def is_running(self):
        """
        Check if there are any workers still alive
        Useful for determining if processes were terminated unexpectedly
        """
        return any(p.is_alive() for p in self.worker_queue)

    # TODO: function to check/poll if any worker process throws error
    # Maybe auto-restart failed workers X num of times
    def monitor_workers(self):
        """
        Monitors and auto-restarts worker mapping to device id if they crash
        """
        while not self.stop_event.is_set():
            for i, worker_info in enumerate(self.worker_queue):
                process = worker_info["process"]
                device_id = worker_info["device_id"]
                port = worker_info["port"]

                # Process crashed, create new worker and restart process
                if not process.is_alive():
                    self.__logger.warning(f"Worker {process.name} crashed. Restarting...")

                    new_worker = CameraWorker(
                        host=self.SERVER_HOST,
                        port=port,
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
                    self.worker_queue[i]["process"] = new_process
            time.sleep(1)
