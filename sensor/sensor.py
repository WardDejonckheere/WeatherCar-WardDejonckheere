import logging
import signal

import threading
import subprocess
import datetime
from time import sleep
import mysql.connector as mariadb

from web.Classes.BMP280 import BMP280
from web.Classes.DHT11 import DHT11
from web.Classes.DS3231 import DS3231
from web.Classes.GYNEO6MV2 import GYNEO6MV2
from web.Classes.RepeatedTimer import RepeatedTimer

log = logging.getLogger(__name__)

running = True

frequency = 2.5

dtime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
print(dtime)
gps = GYNEO6MV2()
clock = DS3231()
dht11 = DHT11(17)
barometer = BMP280()


def save_sensor_value(name, dtime, value):
    try:
        conn = mariadb.connect(database='weathercar_db', user='project1-sensor', password='WeatherCarSensor1684')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO historiek (idHistoriek, Sensor, Datum, Waarde) VALUES (null, %s, %s, %s)", (name, dtime, value))
        conn.commit()
        log.debug("Saved sensor {}={} to database".format(name, value))
        return True
    except Exception as e:
        log.exception("DB update failed: {!s}".format(e))


def setup():
    def shutdown(*args):
        global running
        running = False
        # try:
        #     sys.exit(0)
        # except KeyError as ex:
        #     pass

    signal.signal(signal.SIGTERM, shutdown)

def get_date():
    global dtime
    # dtime = clock.get_datetime()
    dtime = datetime.datetime.now()
    return dtime

def save_temperature():
    value = barometer.read_temperature()
    # get_date()
    save_sensor_value("TP", dtime,value)
    return

def save_humidity():
    value = dht11.get_result()
    if value is None:
        return
    value = value.HUMIDITY_PERC
    # get_date()
    save_sensor_value("HD", dtime, value)

def save_pressure():
    value = barometer.read_pressure()
    # get_date()
    save_sensor_value("PS", dtime, value)
    return

def save_location():
    try:
        value = gps.read_gps()
        latdegr = value.LATDEGREES
        latmin = value.LATMINUTES
        latdirect = value.LATDIRECTION
        longdegr = value.LONGDEGREES
        longmin = value.LONGMINUTES
        longdirect = value.LONGDIRECTION

        # get_date()
        save_sensor_value("GPS lat", dtime, latdegr)
        save_sensor_value("GPS lat min", dtime, latmin)
        save_sensor_value("GPS lat direction", dtime, latdirect)
        save_sensor_value("GPS long", dtime, longdegr)
        save_sensor_value("GPS long min", dtime, longmin)
        save_sensor_value("GPS long direction", dtime, longdirect)
    except:
        # Error finding gps sattelites
        pass
    return

def loop():
    get_date()
    save_temperature()
    # save_humidity()
    save_pressure()
    save_location()
def start_repeat():
    timer = RepeatedTimer(5, loop)



if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    try:
        setup()
        start_repeat()
        while running:
            sleep(1)
    except KeyboardInterrupt:
        pass
