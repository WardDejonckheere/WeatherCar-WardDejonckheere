import RPi.GPIO as GPIO
import time


class Motor():
    def __init__(self, A1, A2):
        GPIO.setwarnings(False)
        self.A1 = A1
        self.A2 = A2
        self.motor = (self.A1, self.A2)
        GPIO.setup(A1, GPIO.OUT)
        GPIO.setup(A2, GPIO.OUT)
        GPIO.output(A1, GPIO.LOW)
        GPIO.output(A2, GPIO.LOW)

    def forward(self):
        # speed = self.speed()
        GPIO.output(self.A1, GPIO.HIGH)
        GPIO.output(self.A2, GPIO.LOW)

    def reverse(self):
        # speed = self.speed()
        GPIO.output(self.A1, GPIO.LOW)
        GPIO.output(self.A2, GPIO.HIGH)

    def off(self):
        GPIO.output(self.A1, GPIO.LOW)
        GPIO.output(self.A2, GPIO.LOW)



def main():
    GPIO.setmode(GPIO.BCM)
    try:
        motorA = Motor(6, 13)
        motorB = Motor(19, 26)
        # motorA.forward()
        # motorB.forward()
        motorA.forward()
        time.sleep(2)
        motorA.reverse()
        time.sleep(2)
        motorA.off()
        motorB.forward()
        time.sleep(2)
        motorB.reverse()
        time.sleep(2)
    except KeyboardInterrupt:
        pass
    finally:
        GPIO.setwarnings(False)  # get rid of warning when no GPIO pins set up
        GPIO.cleanup()


if __name__ == '__main__':
    main()