import opencv
import logging
import socket

import multiprocessing as mp

from enum import Enum

class CameraDeviceController:

    __logger = logging.getLogger(__name__)
    
    def __init__(self):
        """
        Initializes Camera Manager which handles all of the worker processes
        """
        pass
    
    def start_camera_workers():
        """
        Start indiividual processes for each camera device
        """
        pass
    
    def stop_workers():
        """
        Stops all camera processes
        """
        pass
    
    def init_socket():
        """
        Initializes the TCP socket per camera for transmitting data to base terminal
        """
        pass
    
    def init_camera_device():
        """
        Initialize devices for all USB cameras to fetch video/ image data from
        """
        pass