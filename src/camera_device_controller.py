import cv2
import logging
import socket

import multiprocessing as mp

from enum import Enum

class CameraDeviceController:

    __logger = logging.getLogger(__name__)
    
    def __init__(self):
        """
        Initializes Camera Device Controller which manages and handles all of the worker processes
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
    
    def __init_socket():
        """
        Initializes the TCP socket per camera for transmitting data to base terminal
        """
        pass
    
    def __init_camera_device():
        """
        Initialize devices for all USB cameras to fetch video/ image data from
        """
        pass
    