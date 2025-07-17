import logging
# from gpiozero import Button, PWMLED
import RPi.GPIO as GPIO

# from signal import pause
from modules.device_state import DeviceState

class ArmingButton:
    BUTTON_PIN = 17
    RED_PIN = 22
    GREEN_PIN = 23
    BLUE_PIN = 24

    def __init__(
        self,
        stop_event=None,
    ):
        self.__logger = logging.getLogger(__name__)

        # GPIO pin initialization
        self.button_pin = self.BUTTON_PIN
        self.led_pins = {"R": self.RED_PIN, "G": self.GREEN_PIN, "B": self.BLUE_PIN}
        self.stop_event = stop_event
        
        #  cathode

        GPIO.setmode(GPIO.BCM)  # Broadcom e.g. GPIO 12
        GPIO.setup(self.button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # pull up button

        # Setup GPIO for LED colours and set initially off
        for pin in self.led_pins.values():
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.LOW)  # high is off

        self.state = DeviceState.DISARMED  # Initially not armed
        self.set_led_state(self.state)

        # TODO: Update so arming button directly changes state of shared memory or triggers state change

    def wait_for_press(self):
        # Block all events until button is pressed and device armed
        self.__logger.info("Waiting for arming button press...")
        GPIO.wait_for_edge(self.button_pin, GPIO.FALLING)
        time.sleep(0.2)  # delay for debouncing
        self.state = DeviceState.ARMED
        self.set_led_state(self.state)
        self.__logger.info("Button pressed received, system armed")

    def set_colour(self, colour):
        """
        Sets RGB LED colour
        1 = ON, 0 = OFF
        """
        GPIO.output(self.led_pins["R"], GPIO.HIGH if colour == "RED" else GPIO.LOW)
        GPIO.output(self.led_pins["G"], GPIO.HIGH if colour == "GREEN" else GPIO.LOW)
        GPIO.output(self.led_pins["B"], GPIO.HIGH if colour == "BLUE" else GPIO.LOW)

    def set_led_state(self, state: DeviceState):
        """
        Set RGB LED colour based on state
        """
        if state == DeviceState.DISARMED:  # disarmed = red
            self.set_colour("RED")
        elif state == DeviceState.ARMED:  # armed = green
            self.set_colour("GREEN")
        elif state == DeviceState.STATIONARY:  # stationary = blue
            self.set_colour("BLUE")

    def update_state(self, new_state: DeviceState):
        """
        Update state and LED color
        """
        if new_state != self.state:
            self.state = new_state
            self.set_led_state(new_state)
            self.__logger.debug(f"Device state changed to {new_state.name}")

    def cleanup(self):
        GPIO.cleanup()

    def __del__(self):
        self.cleanup()

    # pause()

    # GPIO.setmode(GPIO.BCM)
    # GPIO.setup(red_pin, GPIO.OUT)  # Red
    # GPIO.setup(green_pin, GPIO.OUT)  # Green
    # GPIO.setup(blue_pin, GPIO.OUT)  # Blue

    # self.button = Button(button_pin)  # Switch connected to GPIO17 (edit with pin used)

    # self.red = PWMLED(22)
    # self.green = PWMLED(23)
    # self.blue = PWMLED(24)
#  Currently interrupt not used assuming once armed, button press has no effect
#  def __setup_interrupt_event(self, bouncetime=100):
#         GPIO.add_event_detect(
#             self.button_pin,
#             GPIO.FALLING,
#             callback=self.on_press,
#             bouncetime=bouncetime,  # configure
#         )

#     def on_press(self):
#         self.__logger.info("Arming button pressed")

#         # Set LED colour to red
#         self.set_colour("RED")
#         self.state = DeviceState.DISARMED

#     def on_release(self):
#         # Set LED colour to green (armed)
#         self.set_colour("GREEN")
#         self.state = DeviceState.ARMED

#     # self.button.when_pressed = on_press
#     # self.button.when_release = on_release

#     def toggle_state(self):
#         """
#         Toggle between armed and disarmed state
#         Updates LED colours to match state and calls stop_event for disarm
#         """
#         self.armed = not self.armed

#         if self.armed:
#             print("[Button] System ARMED")
#             self.set_colour(0, 1, 0)  # Set to green
#         else:
#             print("[Button] System DISARMED")
#             self.set_colour(1, 0, 0)  # Set to red
#             if self.stop_event:
#                 print("[Button] Triggering stop_event")
#                 self.stop_event.set()

