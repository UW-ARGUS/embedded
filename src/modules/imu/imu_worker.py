import time
import logging
import board
import busio
import adafruit_icm20x
import socket
import struct
import json
import numpy as np
from ahrs.filters import Madgwick
from multiprocessing import Process
from scipy.spatial.transform import Rotation as R


class IMUWorker:
    """
    IMU data processing for local sensing and to help change states
    """
    SOCKET_RETRY_WINDOW = 10
    SAMPLE_PERIOD = 0.02

    def __init__(self, host, port, stop_event, shared_data, send_mode="json"):
        """
        shared_data: multiprocessing Array of doubles that can hold 9 values (eg. mp.Array('d',9))
        stop_event: multiprocessing event
        """
        self.__logger = logging.getLogger(__name__)

        # TCP server socket connection variables
        self.host = host
        self.port = port
        self.socket = None  
        self.last_reconnect_attempt = 0
        self.send_mode = send_mode # "json" or "binary" (binary packed struct)

        # IMU reading done in its own process to continuously poll sensor data without blocking camera workers
        self.stop_event = stop_event

        # Shared message queue so latest sensor readings and states are tracked and updated to trigger events
        self.shared_data = shared_data
        
        self.madgwick_filter = Madgwick(sampleperiod=self.SAMPLE_PERIOD) # Madgwck filter for estimating orientation
        self.quaternion = np.array([1.0, 0.0, 0.0, 0.0]) # Initial quaternion
        self.gravity_world = np.array([0.0, 0.0, -9.81]) # Acceleration due to gravity in the world frame
        self.socket_process = None # Background socket process for reconnecting
        self.sensor_process = None # Process for sensor data reading

    def setup_process(self):
        self.__logger.info("setting up processes")
        self.sensor_process = Process(target=self.__read_imu_data)
        self.sensor_process.start()
        
        self.__logger.info("setting up socket process")        
        self.socket_process = Process(target=self.__handle_socket_comm)
        self.socket_process.start()
        
    def __read_imu_data(self):
        self.__logger.info("[IMU] Running IMU")

        # Intiailizie ICM 20948 IMU
        try:
            i2c = board.I2C()  # uses board.SCL and board.SDA                
            sensor = adafruit_icm20x.ICM20948(i2c, address=0x69)
            self.__logger.debug("[IMU] IMU sensor initialized")
        except ValueError as e:
            self.__logger.error(f"[IMU] No I2C device found at the given address: {e}")
            return # Return error if no sensor successfully setup

        while not self.stop_event.is_set():
            try:
                # Reads accelereation, gyronometer, and magnetometer sensor data (tuple)
                accel = sensor.acceleration
                gyro = sensor.gyro
                mag = sensor.magnetic

                accel_without_gravity = self.__get_acceleration_data_without_gravity(accel, gyro)

                # Atomically update shared memory
                self.shared_data.set(accel_without_gravity, gyro, mag)

                # Print calibrated values for debugging
                # self.shared_data.print()
                # self.shared_data.print_raw()
                # payload = self.__pack_binary_imu_data()
                # self.__logger.debug(f"binary struct payload: {payload}") # print payload for debuggin

                # json_data = self.__json_imu_data()
                # self.__logger.debug(f"json payload: {json_data}") # print payload for debugging
                time.sleep(self.SAMPLE_PERIOD)
                # time.sleep(1)
            except Exception as e:
                self.__logger.error(f"Error: {e}")
    
    def __get_acceleration_data_without_gravity(
        self,
        acceleration_data: tuple[float, float, float],
        gyroscope_data: tuple[float, float, float],
    ) -> tuple[float, float, float]:
        """
        Removes acceleration due to gravity from the IMU readings.

        Parameters
        ----------
        acceleration_data: The measured acceleration data in X, Y, and Z axes.
        gyroscope_data: The measured angular speed data in X, Y, and Z axes.

        Returns
        -------
        tuple(float, float, float): The calibrated acceleration data in X, Y, and Z axes.
        """
        # Update the Madgwick filter with IMU data
        self.quaternion = self.madgwick_filter.updateIMU(
            self.quaternion,
            gyroscope_data,
            acceleration_data,
        )

        # Convert the quaternion into its corresponding rotation
        rotation_world_to_body = R.from_quat(
            [
                self.quaternion[1],
                self.quaternion[2],
                self.quaternion[3],
                self.quaternion[0],
            ]
        )

        # Get the gravity vector in the body coordinate system
        gravity_body = rotation_world_to_body.apply(self.gravity_world)

        # Get the acceleration data without gravity
        acceleration_data_without_gravity = (
            acceleration_data[0] - gravity_body[0],
            acceleration_data[1] - gravity_body[1],
            acceleration_data[2] - gravity_body[2],
        )
        
        return acceleration_data_without_gravity
    
    def __handle_socket_comm(self):
        
        while not self.stop_event.is_set():
            if self.socket is None:
                self.__retry_socket_conn()
                # self.__logger.debug(f"Attempting to reconnect")
                
            # Check if socket is connected. If not, attempt to reconnect every interval (SOCKET_RETRY_WINDOW)
            # Send data if socket exists
            if self.socket:
                try:
                    self.send_imu_data()
                except (BrokenPipeError, ConnectionResetError) as e:
                    self.__logger.error(f"[IMU] Unable to connect to server: {e}")
                    self.socket = None
            else:
                # Retry socket connection every 5 seconds
                self.__retry_socket_conn()
    
    def run(self):
        """
        Starts IMU sensor reading and socket communication processes
        """
        self.setup_process()
        self.__logger.info("Finished setting up processes")
        
        try: 
            while not self.stop_event.is_set():
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop_event.set()
            self.__logger.info("[IMUWorker] Process interrupted by user")
        
        self.__logger.info("[IMUWorker] Exiting")
        
        # Wait for processes to finish
        # self.sensor_process.join()
        # self.socket_process.join()
        
        # self.__logger.info("Exiting IMU")
                
    def run_old(self):
        self.__logger.info("[IMU] Running IMU")

        # Intiailizie ICM 20948 IMU
        try:
            i2c = board.I2C()  # uses board.SCL and board.SDA
            # self.__logger.debug("Setup i2c board clock and data")
                
            sensor = adafruit_icm20x.ICM20948(i2c, address=0x69)
            self.__logger.debug("[IMU] IMU sensor initialized")
        except ValueError as e:
            self.__logger.error(f"[IMU] No I2C device found at the given address: {e}")
            return # Return error if no sensor successfully setup

        # Run until stop event triggered
        while not self.stop_event.is_set():
            try:
                # Reads accelereation, gyronometer, and magnetometer sensor data (tuple)
                accel = sensor.acceleration
                gyro = sensor.gyro
                mag = sensor.magnetic

                # Atomically update shared memory
                self.shared_data.set(accel, gyro, mag)

                # Print calibrated values for debugging
                # self.shared_data.print()
                self.shared_data.print_raw()
                # payload = self.__pack_binary_imu_data()
                # self.__logger.debug(f"binary struct payload: {payload}") # print payload for debuggin

                # json_data = self.__json_imu_data()
                # self.__logger.debug(f"json payload: {json_data}") # print payload for debugging

                # Check if socket is connected. If not, attempt to reconnect every interval (SOCKET_RETRY_WINDOW)
                # Send data if socket exists
                # if self.socket:
                #     try:
                #         self.send_imu_data()
                #     except (BrokenPipeError, ConnectionResetError) as e:
                #         self.__logger.error(f"[IMU] Unable to connect to server: {e}")
                #         self.socket = None
                # else:
                #     # Retry socket connection every 5 seconds
                #     self.__retry_socket_conn()

            except Exception as e:
                self.__logger.error(f"[IMUWorker] Error: {e}")

            time.sleep(0.02)  # 50 Hz delay
            # time.sleep(1)
        self.__logger.info("[IMUWorker] Exiting")

    def __setup_socket(self):
        """
        Initializes the TCP socket transmitting IMU data to base terminal
        """

        # Initialize network connection
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(10.0)

        try:
            self.__logger.info(f"Connecting to {self.host}:{self.port}")
            self.socket.connect((self.host, self.port))
        except socket.timeout:
            self.__logger.error("[IMU] Connection timed out")
            raise RuntimeError("[IMU] Connection timed out")
        except Exception as e:
            self.__logger.error(f"[IMU] Connection error: {e}")
            raise RuntimeError(f"[IMU] Connection failed: {e}")

        self.__logger.info(f"[IMU] Socket successfully initialized")
    
    def __retry_socket_conn(self):
        current_time = time.time()
        if (current_time - self.last_reconnect_attempt) >= self.SOCKET_RETRY_WINDOW:
            self.last_reconnect_attempt = current_time
            try:
                self.__logger.debug(f"[IMU] Attempting to reconnect to {self.host}:{self.port}")
                
                # Setup TCP socket
                self.__setup_socket()
            except Exception:
                self.__logger.warning("[IMU] Unable to connect to socket, retrying...")
                self.socket = None


    def send_imu_data(self):
        self.__logger.info(f"Sending data: {self.socket}")
        if not self.socket:
            self.__retry_socket_conn()
            return

        # delay_seconds = 2
        try:
            if self.mode == "json":
                # JSON serializable format
                payload = self.__json_imu_data()
            else:
                # Packed data in binary struct
                payload = self.__pack_binary_imu_data()

            # Packed struct
            self.socket.sendall(payload)

            self.__logger.debug("[IMU] Packed data sent successfully")
        except (BrokenPipeError, ConnectionResetError):
            self.socket = None
        except Exception as e:
            self.__logger.error(f"[IMUWorker] Error sending IMU data: {json_err}")

        # time.sleep(delay_seconds)

    def __pack_binary_imu_data(self):
        """
        Pack imu data in struct:

        Payload format:
        - 4 bytes: length of payload (unsigned int, big-endian)
        - 8 bytes: timestamp (float)
        - 1 bytes: state flag (binary, 0 = moving, 1 = stationary)
        - 9 * 4 bytes:  accel, gyro, mag (float, 4 bytes each)
        """
        try:
            # Send raw imu data
            imu_reading = self.shared_data.get_calibrated()
            state_flag = self.shared_data.get_state().value  # State value (moving: 0, stationary: 1)
            timestamp = time.time()

            # Convert to dict with accel, gyro, mag, and time values
            packed_data = struct.pack(
                '>dB9f',
                timestamp,  # current timestamp
                state_flag,  # state
                *(imu_reading.accel),  # x, y, z acceleration values
                *(imu_reading.gyro),
                *(imu_reading.mag)
            )

            # Prefix with 4-byte length header
            return struct.pack('>I', len(packed_data)) + packed_data
        except Exception as e:
            self.__logger.error(f"[IMU] Error packing data: {e}")
            return b''

    def __json_imu_data(self):
        # Send raw imu data
        imu_reading = self.shared_data.get_calibrated()

        # Convert to dict with accel, gyro, mag, and time values
        data = {
            "timestamp": time.time(),
            "state": self.shared_data.get_state().name,
            "accel": imu_reading.accel,
            "gyro": imu_reading.gyro,
            "mag": imu_reading.mag,
        }

        # Convert dict to JSON string
        json_data = json.dumps(data)  
        
        return json_data.encode('utf-8') + b'\n' # Add newline as delimiter

    def stop_imu(self):
        self.stop_event.set()
        if self.socket:
            self.socket.close()

    def __del__(self):
        self.stop_imu()
