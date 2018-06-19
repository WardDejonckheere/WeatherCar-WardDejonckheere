import json
import logging
from RPi import GPIO
from flask import Flask, g, request, abort, flash, render_template, redirect
from flask_socketio import SocketIO, emit
from flaskext.mysql import MySQL
from flask_httpauth import HTTPBasicAuth
from passlib import pwd
from passlib.hash import argon2

from Classes.DHT11 import DHT11
from Classes.DS3231 import DS3231
from Classes.GYNEO6MV2 import GYNEO6MV2
from Classes.HCSR04 import HC_SR04
from Classes.Motor import Motor
from Classes.SERVO import ServoMotor
from Classes.RepeatedTimer import RepeatedTimer

log = logging.getLogger(__name__)
app = Flask(__name__, template_folder='./templates')
mysql = MySQL(app)
auth = HTTPBasicAuth()
socketio = SocketIO(app)

# MySQL configurations
app.config['MYSQL_DATABASE_USER'] = 'project1-web'
app.config['MYSQL_DATABASE_PASSWORD'] = 'WeatherCarWeb8460'
app.config['MYSQL_DATABASE_DB'] = 'weathercar_db'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'

# session config
app.secret_key = pwd.genword(entropy=128)


# Initialising
servo = ServoMotor(5, 3, 11)
motorA = Motor(6, 13)
motorB = Motor(19, 26)
sonicSensor = HC_SR04(27, 18)
motorB.off()
motorA.off()

# Settings
general_settings = {"Time_settings": "12", "Temperature_settings": "Celcius", "Pressure_settings": "Pascal",
                 "Location_settings": "Degrees", "Control_settings": "WASD"}


def save_settings():
    global general_settings
    log.info("Saving settings")
    try:
        file = open("settings.txt", "w+")
        file.write(str(general_settings))
        file.close()
    except Exception as ex:
        log.exception("Failed to save settings: %s" % ex)


def get_data(sql, params=None):
    conn = mysql.connect()
    cursor = conn.cursor()
    records = []
    try:
        cursor.execute(sql, params)
        result = cursor.fetchall()
        for row in result:
            records.append(list(row))
    except Exception as e:
        log.exception("Fout bij het ophalen van data: {0})".format(e))

    cursor.close()
    conn.close()
    return records


def get_last_row_data(sensor):
    value = get_data("SELECT Waarde FROM historiek WHERE Sensor = %(sensor)s ORDER BY idHistoriek DESC LIMIT 1", {'sensor': sensor})
    value = value[0][0]
    return value


def data_compare(sensor, value):
    if sensor == "temperature":
        db_sensor = "TP"
    elif sensor == "humidity":
        db_sensor = "HD"
    elif sensor == "pressure":
        db_sensor = "PS"

    data = get_data("SELECT count(*), sum(Waarde) from historiek where Sensor = %(sensor)s and Datum >= DATE_SUB(NOW(),"
                    " INTERVAL 1 HOUR);", {'sensor': db_sensor})

    try:
        data = data[0]
        if data[0] == 0:
            return 0
        value = float(value)
        average = data[1] / data[0]
        difference = abs(value - average)
        if difference >= 0.01 * average:
            if value > average:
                trend = 1
            else:
                trend = -1
        else:
            trend = 0
    except Exception as ex:
        log.exception("Failed to get trend: %s" % ex)
        trend = 0

    return trend


def refresh_data_home():
    try:
        temperature = float(get_last_row_data("tp"))
        temperature_trend = data_compare("temperature", temperature)
        if general_settings["Temperature_settings"] == "Celcius":
            temperature = str(round(temperature)) + "°C"
        elif general_settings["Temperature_settings"] == "Fahrenheit":
            temperature = str(round(temperature * 1.8 + 32)) + "°F"
    except Exception as ex:
        log.exception("failed to refresh temperature: %s" % ex)
        temperature = "?"

    try:
        humidity = get_last_row_data("HD")
        humidity_trend = data_compare("humidity", humidity)
        humidity += "%"
    except Exception as ex:
        log.exception("failed to refresh humidity: %s" % ex)
        humidity = "?"

    try:
        pressure = get_last_row_data("PS")
        pressure_trend = data_compare("pressure", pressure)
        if general_settings["Pressure_settings"] == "Pascal":
            pressure = float(pressure) / 1000
            pressure = str(round(pressure, 1)) + "kPa"
        elif general_settings["Pressure_settings"] == "Bar":
            pressure = float(pressure) / 100000
            pressure = round(pressure, 4)
            pressure = str(pressure) + "B"
    except Exception as ex:
        log.exception("failed to refresh pressure: %s" % ex)
        pressure = "?"

    try:
        gpslatdeg = str(get_last_row_data("GPS lat"))
        gpslatmin = str(get_last_row_data("GPS lat min"))
        gpslator = get_last_row_data("GPS lat direction")
        gpslongdeg = str(get_last_row_data("GPS long"))
        gpslongmin = str(get_last_row_data("GPS long min"))
        gpslongor = get_last_row_data("GPS long direction")
        if general_settings["Location_settings"] == "Degrees":
            lat = gpslatdeg + "°" + str(round(float(gpslatmin), 1))+ "'" + gpslator
            long = gpslongdeg + "°" + str(round(float(gpslongmin), 1)) + "'" + gpslongor
        elif general_settings["Location_settings"] == "Decimal":
            lat = str(round(int(gpslatdeg) + float(gpslatmin) / 60, 3)) + gpslator
            long = str(round(int(gpslongdeg) + float(gpslongmin) / 60, 3)) + gpslongor
    except Exception as ex:
        log.exception("failed to refresh location: %s" % ex)
        lat = "?"
        long = "?"

    dict_data = '{"temperature":["%s", %d], "humidity":["%s", %d], "pressure":["%s", %d], "gpslat":"%s", ' \
                '"gpslong":"%s"}' \
                % (temperature, temperature_trend, humidity, humidity_trend, pressure, pressure_trend, lat, long)

    socketio.emit("my data",
                  dict_data,
                  namespace='/datahome')


def get_data_interval(sensor, interval=12, amount=9999):
    data = get_data("SELECT * FROM (SELECT @row := @row +1 AS rownum, Waarde, Datum FROM(SELECT @row :=0) r, historiek "
                    "WHERE Sensor = %(sensor)s and Datum >= DATE_SUB(NOW(), INTERVAL 1 HOUR)) ranked "
                    "WHERE rownum %% %(rows)s = 1 ORDER BY rownum DESC limit %(max)s",
                    {"sensor": sensor, "rows": interval, "max": amount})
    return data


def get_data_chart(sensor):
    data = get_data_interval(sensor)
    data_chart = {"labels":[], "data":[]}
    try:
        data = reversed(data)
        for i in data:
            dtime = i[2]
            if general_settings["Time_settings"] == "24":
                time_test = dtime.strftime("%d-%m %H:%M")
            elif general_settings["Time_settings"] == "12":
                time_test = dtime.strftime("%d-%m %I:%M%p")
            data_chart["labels"].append(time_test)
            value = float(i[1])
            if sensor == "TP":
                if general_settings["Temperature_settings"] == "Celcius":
                    value = value
                elif general_settings["Temperature_settings"] == "Fahrenheit":
                    value = value * 1.8 + 32
            elif sensor == "PS":
                if general_settings["Pressure_settings"] == "Pascal":
                    value = float(value) / 1000
                elif general_settings["Pressure_settings"] == "Bar":
                    value = float(value) / 100000
            data_chart["data"].append(value)
    except Exception as ex:
        log.exception("Failed to get data for chart: %s" % ex)

    return data_chart


def load_settings():
    global general_settings
    log.info("Loading settings from file")
    try:
        file = open("settings.txt")
        line = file.read()
        line = line.replace("'", '"')
        general_settings = json.loads(line)
    except Exception as ex:
        log.exception("Failed to load settings, using defaults: %s" % ex)


timer = RepeatedTimer(0.5, refresh_data_home)


@app.route('/')
def index():
    log.info("Loading home page")
    load_settings()
    return render_template("home.html")


@app.route('/controls')
def controls():
    log.info("Loading control page")
    load_settings()
    return render_template("controls.html", settings_controls=general_settings["Control_settings"])


@app.route('/data')
def data():
    log.info("Loading data page")
    load_settings()
    data_chart = {"temperature": get_data_chart("TP"), "humidity": get_data_chart("HD"),
                  "pressure": get_data_chart("PS")}
    return render_template("data.html", data_chart=data_chart, general_settings=general_settings)


@app.route('/settings')
def settings():
    log.info("Loading settings page")
    load_settings()
    return render_template("settings.html", current_settings=general_settings)


@socketio.on("connect")
def connect():
    log.info("Client connected to socket")


@socketio.on("forwards", namespace='/control')
def forwards(control):
    motorA.forward()
    motorB.forward()
    log.debug("Forwards")
    return 'Nothing'


@socketio.on("backwards", namespace='/control')
def backwards(control):
    log.debug("Backwards/Reverse")
    motorA.reverse()
    motorB.reverse()
    return 'Nothing'


@socketio.on("left", namespace='/control')
def left(control):
    log.debug("Turning Left")
    servo.set_angle(-45)
    return 'Nothing'


@socketio.on("right", namespace='/control')
def right(control):
    log.debug("Turning Right")
    servo.set_angle(45)
    return 'Nothing'


@socketio.on("stop", namespace='/control')
def stop(control):
    log.debug("Stopping movement")
    motorA.off()
    motorB.off()
    return 'Nothing'


@socketio.on("stopturn", namespace='/control')
def stopturn(control):
    log.debug("Stopped Turning")



    servo.set_angle(0)
    return 'Nothing'


@socketio.on("settings", namespace='/settings')
def settings(setting):
    global general_settings
    general_settings = setting
    save_settings()
    return


if __name__ == '__main__':
    GPIO.setwarnings(False)
    logging.basicConfig(level=logging.WARNING, filename="Logging_Web.txt")
    log.info("Flask app starting")
    socketio.run(app, host='192.168.0.142', debug=False)
