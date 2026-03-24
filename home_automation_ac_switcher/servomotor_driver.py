import RPi.GPIO as GPIO  # Imports the standard Raspberry Pi GPIO library
from time import sleep   # Imports sleep (aka wait or pause) into the program
from RPi.GPIO import PWM

PWM_PIN_FOR_SERVO = 32

    

#For DEAO servomotor
#2.0 min(0 degrees) - 13-max(180 degrees)
def rotate_to_angle_in_pulse_width_and_return(pulse_width):
    GPIO.setmode(GPIO.BOARD) # Sets the pin numbering system to use the physical layout
    # Set up pin for PWM
    GPIO.setup(PWM_PIN_FOR_SERVO,GPIO.OUT)  # Sets up pin to an output (instead of an input)
    p = GPIO.PWM(PWM_PIN_FOR_SERVO, 50)     # Sets up pin as a PWM pin
    p.start(0)               # Starts running PWM on the pin and sets it to 0
    sleep(1.5)
    p.ChangeDutyCycle(3)    # Changes the pulse width to (so moves the servo)
    sleep(1.5)
    p.ChangeDutyCycle(pulse_width)    # Changes the pulse width to (so moves the servo)
    sleep(2)
    p.ChangeDutyCycle(3)    # Changes the pulse width to (so moves the servo)
    sleep(1.5)

    # Clean up
    p.stop()                 # At the end of the program, stop the PWM
    GPIO.cleanup(PWM_PIN_FOR_SERVO)

