import cv2
import socket
import struct
import time
import logging


class CameraWorker:
    def __init__(
        self,
        device_id: int,
        port: int,
        host: int,
        fps: float,
        stop_event,  # multiprocessing event for when workers should stop streaming data
    ):
        """
        Initialize camera worker for current camera device Id and TCP port
        """
        self.id = device_id
        self.port = port
        self.host = host
        self.fps = fps
        self.camera = None  # OpenCV camera object
        self.socket = None  # TCP server socket
        self.stop_event = stop_event
        self.height = 320
        self.width = 240

        logging.basicConfig(level=logging.DEBUG)
        self.__logger = logging.getLogger(__name__)

    def run_camera(self):
        """
        Starts the camera and setups the TCP socket. Then attempts to transmit frames over socket
        Once finished or error encountered, cleans up by releaseing resources
        """
        try:
            self.__setup_camera()
            self.__logger.info(f"Finished camera setup, setting up sockets\n")
            self.__setup_socket()
            self.__stream_frames()
        except Exception as e:
            self.__logger.exception(f"Camera-{self.id}] Error: {e}")
        finally:
            self.__del__()

    def __setup_camera(self):
        """
        Initializes USB camera by opening the device
        TODO: Potentially add setting camera resolution
        """

        self.camera = cv2.VideoCapture(self.id)
        self.camera.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))

        if not self.camera.isOpened():
            raise RuntimeError("Failed to open camera")

        # set resolution
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)

        self.__logger.info(f"[Camera-{self.id}] Camera successfully initialized")

    def __setup_socket(self):
        """
        Initializes the TCP socket per camera for transmitting data to base terminal
        """

        # Initialize network connection
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(60.0)
        RETRY_WINDOW = 10

        while not self.stop_event.is_set():
            try:
                self.__logger.info(f"Connecting to {self.host}:{self.port}")
                self.socket.connect((self.host, self.port))
                logging.info(f"Camera {self.id} socket initialized\n")
                return
            except ConnectionRefusedError:
                 self.__logger.warning(f"[Camera-{self.id}] Connection refused, retrying in {RETRY_WINDOW}s...\n")
            except socket.timeout:
                self.__logger.warning(f"[Camera-{self.id}] Connection timed out, retrying in {RETRY_WINDOW}s...\n")
            except Exception as e:
                self.__logger.error(f"[Camera-{self.id}] Unexpected error: {e}, retrying in {RETRY_WINDOW}s...\n")

            time.sleep(RETRY_WINDOW)
            
    def retry_frame_read(self, retries=3, delay=0.1):
        for _ in range(retries):
            result, frame = self.camera.read()
            if result:
                return result, frame
            time.sleep(delay)
        self.__logger.warn(f"[Camera-{self.id}] Failed to capture frame after retries")
        return False, None
            
    def stream_single_frame(self):
        # Capture frame
        try:
            # result, frame = self.camera.read()
            result, frame = self.retry_frame_read()
            self.__logger.debug(f"Sending data {result}")
        except Exception as e:
            self.__logger.error(f"Error reading camera-{self.id}: {e}")

        if not result:
            self.__logger.warn(f"[Camera-{self.id}] Failed to capture frame {result}")
            return

        # Encode frame
        result, encoded_frame = cv2.imencode(".jpg", frame)

        if not result:
            self.__logger.warn(f"[Camera-{self.id}] Failed to encode frame")
            return

        data_to_send = encoded_frame.tobytes()

        # Transmit image
        timestamp = time.time()
        length = len(data_to_send)

        # Pack header (timestamp + length)
        header = struct.pack(
            ">dII",  # Big endian (network endianess), float64, uint32, uint32
            timestamp,
            self.id,
            length,
        )

        try:
            # Send header + image to server
            payload = header + data_to_send
            self.socket.sendall(payload)
            self.__logger.info(f"[Camera-{self.id}] payload sent")
        except (BrokenPipeError, ConnectionResetError):
            self.__logger.error(f"[Camera-{self.id}] Unable to connect to server")
            return
        
    def __stream_frames(self):
        """
        Continuously capture and transmit frames over TCP

        Payload format:
        - 8 bytes: timestamp (float)
        - 4 bytes: image length (int)
        - N bytes: encoded image frame
        """
        # delay_seconds = float(1.0 / self.fps)
        delay_seconds = 1.0/max(self.fps, 1.0)

        while not self.stop_event.is_set():
            # Capture frame
            # result, frame = self.camera.read()
            result, frame = self.retry_frame_read()
            self.__logger.debug(f"Sending data {result}")

            if not result:
                self.__logger.warn(f"[Camera-{self.id}] Failed to capture frame {result}")
                continue

            # Encode frame
            result, encoded_frame = cv2.imencode(".jpg", frame)

            if not result:
                self.__logger.warn(f"[Camera-{self.id}] Failed to encode frame")
                continue

            data_to_send = encoded_frame.tobytes()

            # Transmit image
            timestamp = time.time()
            length = len(data_to_send)

            # Pack header (timestamp + length)
            header = struct.pack(
                ">dII",  # Big endian (network endianess), float64, uint32, uint32
                timestamp,
                self.id,
                length,
            )

            try:
                # Send header + image to server
                payload = header + data_to_send
                self.socket.sendall(payload)
                self.__logger.info(f"[Camera-{self.id}] payload sent")
            except (BrokenPipeError, ConnectionResetError):
                self.__logger.error(f"[Camera-{self.id}] Unable to connect to server")
                break

            time.sleep(delay_seconds)

    def __del__(self):
        """
        Releases camera and socket resources
        """
        self.__logger.info(f"[Camera-{self.id}] Releasing socket")

        
        if self.camera:
            self.camera.release()
        if self.socket:
            # Try disabling communication first, gracefully ends if the socket is not already closed
            try:
                self.socket.shutdown(socket.SHUT_RDWR)
            except Exception:
                pass
            
            self.__logger.info(f"[Camera-{self.id}] Closing socket")

            # Close and release the socket
            self.socket.close()

        self.__logger.info(f"[Camera-{self.id}] Camera and socket closed, exiting")
