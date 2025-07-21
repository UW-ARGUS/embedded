import logging
# from gpiozero import Button, PWMLED
import RPi.GPIO as GPIO
import time

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
        polling_interval=0.05
    ):
        self.__logger = logging.getLogger(__name__)

        # GPIO pin initialization
        self.button_pin = self.BUTTON_PIN
        self.led_pins = {"R": self.RED_PIN, "G": self.GREEN_PIN, "B": self.BLUE_PIN}
        self.stop_event = stop_event
        
        #  cathode
        self.polling_interval = polling_interval
        self.last_button_state = GPIO.HIGH  # Button is unpressed (default state)
        self.debounce_delay = 0.2  # 200 ms debounce time

        GPIO.setmode(GPIO.BCM)  # Broadcom e.g. GPIO 12
        # GPIO.setup(self.button_pin, GPIO.IN) #, pull_up_down=GPIO.PUD_UP)  # pull up button
        GPIO.setup(self.button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        # Setup GPIO for LED colours and set initially off
        for pin in self.led_pins.values():
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.LOW)  # high is off

        self.state = DeviceState.DISARMED  # Initially not armed
        self.set_led_state(self.state)

        # TODO: Update so arming button directly changes state of shared memory or triggers state change

    def button_press(self, channel):
        if GPIO.input(self.button_pin) == GPIO.LOW:
            self.__logger.info("Button pressed")
        else:
            self.__logger.info("Button released")
    
    def wait_for_press(self):
        GPIO.remove_event_detect(self.button_pin)  # Remove any existing detection
        GPIO.add_event_detect(self.button_pin, GPIO.BOTH, callback=self.button_press, bouncetime=100)
        
            
    def wait_for_press_2(self):
        # Block all events until button is pressed and device armed
        self.__logger.info("Waiting for arming button press...")
        while True:
            if GPIO.input(self.button_pin) == GPIO.LOW:  # Button is pressed (GPIO input will be LOW)
                time.sleep(0.2)  # Debounce delay
                self.state = DeviceState.ARMED
                self.set_led_state(self.state)
                self.__logger.info("Button pressed received, system armed")
                break
            time.sleep(0.01)  # Polling rate
            self.__logger.info(f"Button: {GPIO.input(self.button_pin)}")
        # GPIO.wait_for_edge(self.button_pin, GPIO.FALLING)
        # # time.sleep(0.2)  # delay for debouncing
        # self.state = DeviceState.ARMED
        # self.set_led_state(self.state)
        # self.__logger.info("Button pressed received, system armed")
        
    def poll_button(self):
        """
        Poll the button state and handle debouncing manually.
        """
        
        button_state = GPIO.input(self.button_pin)  # Read button state (HIGH = unpressed, LOW = pressed)
        # self.__logger.debug(f"Polling button {button_state}")

        if button_state != self.last_button_state:  # Only check if state has changed
            self.__logger.debug(f"Button state changed: {button_state}")

            # If the button was pressed (falling edge)
            if button_state == GPIO.LOW:
                self.on_press()

            # Debounce delay
            time.sleep(self.debounce_delay)  # wait for debounce time before accepting next state change

        self.last_button_state = button_state  # Update the last state
        
    def on_press(self):
        """
        Called when the button is pressed (falling edge).
        """
        self.__logger.info("Button press detected.")
        self.state = DeviceState.ARMED  # Update the device state to ARMED
        self.set_led_state(self.state)
        self.__logger.info("System armed.")
    
    def run(self):
        """
        Main loop to continuously poll for button presses.
        """
        try:
            while True:
                self.poll_button()  # Poll the button state
                time.sleep(self.polling_interval)  # Sleep to avoid high CPU usage
        except KeyboardInterrupt:
            self.__logger.info("Exiting program.")
            self.cleanup()


    def set_colour(self, colour):
        """
        Sets RGB LED colour
        1 = ON, 0 = OFF
        """
        GPIO.output(self.led_pins["R"], GPIO.LOW if colour == "RED" else GPIO.HIGH)
        GPIO.output(self.led_pins["G"], GPIO.LOW if colour == "GREEN" else GPIO.HIGH)
        GPIO.output(self.led_pins["B"], GPIO.LOW if colour == "BLUE" else GPIO.HIGH)

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

