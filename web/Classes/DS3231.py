import logging
from smbus import SMBus
import datetime

from RPi import GPIO

DS3231_DEFAULT_ADDRESS = 0x68

# Registers
DS3231_REG_SECONDS = DS3231_REG_DATETIME = 0x0
DS3231_REG_MINUTES = 0x1
DS3231_REG_HOURS = 0x2
DS3231_REG_DAY = 0x3
DS3231_REG_DATE = 0x4
DS3231_REG_MONTH = 0x5
DS3231_REG_YEAR = 0x6
DS3231_REG_ALARM1_SECONDS = DS3231_REG_ALARM1 = 0x7
DS3231_REG_ALARM1_MINUTES = 0x8
DS3231_REG_ALARM1_HOURS = 0x9
DS3231_REG_ALARM1_DAY_DATE = 0xA
DS3231_REG_ALARM2_MINUTES = 0xB
DS3231_REG_ALARM2_HOURS = 0xC
DS3231_REG_ALARM2_DAY_DATE = 0xD
DS3231_REG_CONTROL = 0xE
DS3231_REG_STATUS = 0xF
DS3231_REG_TEMP_MSB = 0x11
DS3231_REG_TEMP_LSB = 0x12


class DS3231:
    def __init__(self, address=DS3231_DEFAULT_ADDRESS):
        self.i2c = SMBus()
        self.i2c.open(1)
        self.address = address
        logging.info("Klasse geinitialliseerd")

    @property
    def clock_enabled(self):
        value = self.i2c.read_byte_data(self.address, DS3231_REG_CONTROL)
        value = value >> 7
        if value == 1:
            logging.info("Clock is off")
            return False
        else:
            logging.info("Clock is on")
            return True

    @clock_enabled.setter
    def clock_enabled(self, value):
        if value == 0:
            current_settings = self.i2c.read_byte_data(self.address, DS3231_REG_CONTROL)
            logging.debug("Current control: %s" % current_settings)
            new_settings = current_settings | 0b10000000
            logging.debug("New control: %s" % new_settings)
            logging.info("Clock disabled")
            self.i2c.write_byte_data(self.address, DS3231_REG_CONTROL, new_settings)
        else:
            current_settings = self.i2c.read_byte_data(self.address, DS3231_REG_CONTROL)
            logging.debug("Current control: %s" % current_settings)
            new_settings = current_settings & 0b01111111
            logging.debug("New control: %s" % new_settings)
            logging.info("Clock enabled")
            self.i2c.write_byte_data(self.address, DS3231_REG_CONTROL, new_settings)
        
    def get_datetime(self):
        try:
            year = 2000 + self.bcd2int(self.i2c.read_byte_data(self.address, DS3231_REG_YEAR))
            month = self.bcd2int(self.i2c.read_byte_data(self.address, DS3231_REG_MONTH))
            day = self.bcd2int(self.i2c.read_byte_data(self.address, DS3231_REG_DATE))
            hour = self.bcd2int(self.i2c.read_byte_data(self.address, DS3231_REG_HOURS))
            minute = self.bcd2int(self.i2c.read_byte_data(self.address, DS3231_REG_MINUTES))
            sec = self.bcd2int(self.i2c.read_byte_data(self.address, DS3231_REG_SECONDS))
            time = datetime.datetime(year, month, day, hour, minute, sec)
            logging.debug("Got datetime from module: %s" % time)
            return time
        except Exception as ex:
            logging.error("Error getting datetime: %s" % ex)

    def set_datetime(self, value=None):
        try:
            if value:
                if isinstance(value, datetime):
                    date = value
                else:
                    date = datetime.datetime.now()
            else:
                date = datetime.datetime.now()
            self.i2c.write_byte_data(self.address, DS3231_REG_YEAR, self.int2bcd(date.year - 2000))
            self.i2c.write_byte_data(self.address, DS3231_REG_MONTH, self.int2bcd(date.month))
            self.i2c.write_byte_data(self.address, DS3231_REG_DATE, self.int2bcd(date.day))
            self.i2c.write_byte_data(self.address, DS3231_REG_HOURS, self.int2bcd(date.hour))
            self.i2c.write_byte_data(self.address, DS3231_REG_MINUTES, self.int2bcd(date.minute))
            self.i2c.write_byte_data(self.address, DS3231_REG_SECONDS, self.int2bcd(date.second))
            logging.info("Datetime set: %s" % date)
        except Exception as ex:
            logging.error("Error setting datetime: %s" % ex)

    @staticmethod
    def int2bcd(value):
        bcd = (int(value / 10)) << 4
        bcd += value % 10
        return bcd

    @staticmethod
    def bcd2int(value):
        t = value >> 4
        e = (value & 0b00001111)
        n = t * 10 + e
        return n


def main():
    try:
        klok = DS3231()
        print(klok.get_datetime())
    except KeyboardInterrupt:
        pass
    finally:
        GPIO.cleanup()


if __name__ == '__main__':
    main()