import cv2
import socket
import struct
import time
import logging

class Camera_Worker:
    def __init__(
            self,
            device_id: int,
            port: int,
            host: int,
            fps: float
        ):
        """
        Initialize camera worker for current camera device Id and TCP port
        """
        self.id = device_id
        self.port = port
        self.host = host
        self.fps = fps
        self.camera = None # OpenCV camera object
        self.socket = None  # TCP server socket
        
        logging.basicConfig(
            level=logging.DEBUG
        )
        self.__logger = logging.getLogger(__name__)
        
        # self.Width = 1080
        
    def run_camera(self):
        """
        Starts the camera and setups the TCP socket. Then attempts to transmit frames over socket
        Once finished or error encountered, cleans up by releaseing resources
        """
        try:
            self.__setup_camera()
            self.__setup_socket()
            self.__stream_frames()
        except Exception as e:
            self.__logger.error(f"Camera-{self.id}] Error: {e}")
        finally:
            self.__cleanup()
        
    def __setup_camera(self):
        """
        Initializes USB camera by opening the device
        TODO: Potentially add setting camera resolution
        """
        
        self.camera = cv2.VideoCapture(self.id)
        
        if not self.camera.isOpened():
            raise RuntimeError(f"Failed to open camera")
        
        # resolution
        # self.camera.set(cv2.CAPT_PROP_FRAME_WIDTH, self.Width)
        
        self.__logger.info(f"[Camera-{self.id}] Camera successfully initialized")
        
    def __setup_socket(self):
        """
        Initializes the TCP socket per camera for transmitting data to base terminal
        """
        
        # Initialize network connection
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(10.0)

        try:
            self.__logger.info(f"Connecting to {self.host}:{self.port}")
            self.socket.connect((self.host, self.port))
        except socket.timeout:
            self.__logger.error("Connection timed out")
            raise RuntimeError(f"Connection timed out")

        except Exception as e:
            self.__logger.error(f"Connection error: {e}")
            raise RuntimeError(f"Connection failed: {e}")
        
        self.__logger.info(f"Camera {self.id} socket initialized!")

    def __stream_frames(self):
        """
        Continuously capture and transmit frames over TCP
        
        Payload format:
        - 8 bytes: timestamp (float)
        - 4 bytes: image length (int)
        - N bytes: encoded image frame
        """
        delay = float(1.0/ self.fps)
        
        while True:
            # Capture frame
            result, frame = self.camera.read()

            if not result:
                self.__logger.warn(f"[Camera-{self.id}] Failed to capture frame")
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
                ">dI",  # Big endian (network endianess), float64, uint32
                timestamp,
                length,
            )

            try:
                # Send header + image to server
                payload = header + data_to_send
                self.socket.sendall(payload)
            except (BrokenPipeError, ConnectionResetError):
                self.__logger.error(f"[Camera-{self.id}] Unable to connect to server")
                break
            
            time.sleep(delay)
    
    def __cleanup(self):
        """
        Releases camera and socket resources
        """
        if self.camera:
            self.camera.release()
        if self.socket:
            self.socket.close()
        
        self.__logger.info(f"[Camera-{self.id}] Camera and socket closed, exiting")