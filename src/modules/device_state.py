from enum import Enum

class DeviceState(Enum):
    DISARMED = 0
    ARMED = 1
    MOVING = 2
    STATIONARY = 3