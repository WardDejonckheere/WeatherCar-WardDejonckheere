from collections import namedtuple
from serial import Serial
import time
import datetime

Data = namedtuple('GYNEO6MV2Data', 'TIME LAT LATOR LONG LONGOR QT SATS HEIGHT')
Position = namedtuple('GYNEO6MV2Position', 'TIME LATDEGREES LATMINUTES LATDIRECTION LONGDEGREES LONGMINUTES LONGDIRECTION')
class GYNEO6MV2:
    def __init__(self, device="/dev/ttyAMA0", baud=9600):
        self.port = Serial(device, baud)
        self.setup()


    def setup(self):
        line = "$PUBX,00*33"
        bytes = line.encode()
        self.port.write(bytes)

    def read_gps(self, trials=2):
        faults = 0
        self.port.flushInput()
        while True:
            if faults == trials:
                # log("Too much time before read")
                return None
            line = ""
            try:
                while line == "":
                    try:
                        line = self.port.readline()
                        line = line.decode()
                        line = line.rstrip("\r\n")
                    except Exception as ex:
                        # print("bad line")
                        # log exception?
                        line = ""
                        faults += 1
                        if faults == trials:
                            return None
                if line.startswith("$GPGGA"):
                    data = line.rsplit(",")
                    time = round(float(data[1]))
                    lat = round(float(data[2]), 10)
                    lator = data[3]
                    long = round(float(data[4]), 10)
                    longor = data[5]
                    qt = int(data[6])
                    sats = int(data[7])
                    height = float(data[9])
                    data = Data(time, lat, lator, long, longor, qt, sats, height)
                    latd = self.get_degrees_minutes(lat)[0]
                    latm = self.get_degrees_minutes(lat)[1]
                    longd = self.get_degrees_minutes(long)[0]
                    longm = self.get_degrees_minutes(long)[1]
                    self.get_degrees_minutes(long)
                    position = Position(time, latd, latm, lator, longd, longm, longor)  # Adding int() to time stops program from working?
                    return position
                else:
                    pass
            except Exception as x:
                faults += 1
                # print(x)

    @staticmethod
    def get_degrees_minutes(value):
        """Due to python not saving leading 0's, i had to make this function that checks how long de the part before
        the comma is, if this is 3, the format is Dmm.mmmmm else it's DDmm.mmmmm.
        This function returns the right amount of degrees and minutes"""
        split = str(value).rsplit(".")
        if len(split[0]) == 3:
            degrees = split[0][0]
            minutes = split[0][1:3] + ".%s" % (split[1])
        else:
            degrees = split[0][0:2]
            minutes = split[0][2:4] + ".%s" % (split[1])
        return degrees, minutes


def main():
    try:
        gps = GYNEO6MV2()
        while True:
            # value = 332.16204
            # gps.get_degrees_minutes(value)
            # print("value: {0:015.6f}".format(value))
            print(gps.read_gps())
            time.sleep(3)
    except KeyboardInterrupt:
        pass
    finally:
        pass


if __name__ == '__main__':
    main()
