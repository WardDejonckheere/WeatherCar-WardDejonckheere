import time
from RPi import GPIO

class ServoMotor():
    def __init__(self, pin, min_duty, max_duty):
        """Initialize PWM pin for servo motor
        :param pin: GPIO pin for servo control signal
        """
        GPIO.setwarnings(False)
        GPIO.setup(pin, GPIO.OUT)
        self.pin = pin
        self.min_duty = min_duty
        self.max_duty = max_duty
        self.center = min_duty + (max_duty - min_duty) / 2
        self.pwm_servo = GPIO.PWM(pin, 50)
        self.duty_cycle = self.center
        self.pwm_servo.start(self.center)
        time.sleep(1)
        self.pwm_servo.stop()

    def set_angle(self, value):
        """Set servo motor angle
        :param value: angle (-90 -> 90 deg.)
        """
        if not value >= -90 and value <= 90:
            raise ValueError('Servo angle must be between -90 and 90 degrees')
        value += 90
        value = value / 180
        value = value * (self.max_duty - self.min_duty)
        value = value + self.min_duty
        # self.pwm_servo.ChangeDutyCycle(value)
        self.pwm_servo = GPIO.PWM(self.pin, 50)
        self.pwm_servo.start(value)
        time.sleep(0.3)
        self.pwm_servo.stop()

    @staticmethod
    def value_to_angle(value):
        """Convert a 10-bit measurement to a servo angle
        :param value: ADC measurement (0-1023)
        :return: Servo angle (-90 -> 90 deg.)
        """
        return value / 1023 * 180 - 90

def main():
    GPIO.setmode(GPIO.BCM)
    try:
        servo = ServoMotor(5, 3, 11)
        # servo.set_angle(0)
        time.sleep(2)
        while True:
            servo.set_angle(-45)
            time.sleep(1)
            servo.set_angle(45)
            time.sleep(1)

    except KeyboardInterrupt:
        pass
    finally:
        GPIO.setwarnings(False)  # get rid of warning when no GPIO pins set up
        GPIO.cleanup()


if __name__ == '__main__':
    main()