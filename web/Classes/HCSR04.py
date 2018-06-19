import RPi.GPIO as GPIO
import time

class HC_SR04:

    def __init__(self, trigger, echo):
        GPIO.setwarnings(False)
        self.trigger = trigger
        self.echo = echo
        GPIO.setup(self.trigger, GPIO.OUT)
        GPIO.setup(self.echo, GPIO.IN)

    def distance(self):
        GPIO.output(self.trigger, True)
        time.sleep(0.00001)
        GPIO.output(self.trigger, False)
        Startime = time.time()
        StopTime = time.time()
        while GPIO.input(self.echo) == 0:
            Startime = time.time()
        while GPIO.input(self.echo) == 1:
            StopTime = time.time()
        TimeBetween = StopTime - Startime
        distance = (TimeBetween * 34300) /2
        return distance


def main():
    GPIO.setmode(GPIO.BCM)
    afstandsmeter = HC_SR04(27, 18)
    try:
        # Hier kan je jouw functies/klassen oproepen om ze te testen
        while(1):
            print("De afstand is {0:.2f} cm".format(afstandsmeter.distance()))
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        GPIO.setwarnings(False)  # get rid of warning when no GPIO pins set up
        GPIO.cleanup()


if __name__ == '__main__':
    main()