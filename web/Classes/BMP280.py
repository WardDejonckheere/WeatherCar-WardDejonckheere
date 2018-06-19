from RPi import GPIO
from smbus import SMBus

# registers
# BMP280 default address.
BMP280_DEFAULT_ADRESS = 0x76
BMP280_CHIPID = 0xD0

# BMP280 Registers
BMP280_DIG_T1 = 0x88  # R   Unsigned Calibration data (16 bits)
BMP280_DIG_T2 = 0x8A  # R   Signed Calibration data (16 bits)
BMP280_DIG_T3 = 0x8C  # R   Signed Calibration data (16 bits)
BMP280_DIG_P1 = 0x8E  # R   Unsigned Calibration data (16 bits)
BMP280_DIG_P2 = 0x90  # R   Signed Calibration data (16 bits)
BMP280_DIG_P3 = 0x92  # R   Signed Calibration data (16 bits)
BMP280_DIG_P4 = 0x94  # R   Signed Calibration data (16 bits)
BMP280_DIG_P5 = 0x96  # R   Signed Calibration data (16 bits)
BMP280_DIG_P6 = 0x98  # R   Signed Calibration data (16 bits)
BMP280_DIG_P7 = 0x9A  # R   Signed Calibration data (16 bits)
BMP280_DIG_P8 = 0x9C  # R   Signed Calibration data (16 bits)
BMP280_DIG_P9 = 0x9E  # R   Signed Calibration data (16 bits)

BMP280_CONTROL = 0xF4
BMP280_RESET = 0xE0
BMP280_CONFIG = 0xF5
BMP280_PRESSUREDATA = 0xF7
BMP280_TEMPDATA = 0xFA

class BMP280:
    def __init__(self, address=BMP280_DEFAULT_ADRESS):
        self.i2c = SMBus()
        self.i2c.open(1)
        self.address = address
        self._load_calibration()
        self.i2c.write_byte_data(self.address, BMP280_CONTROL, 0x3F)

    def i2c_check(self):
        """Output should be 88, if not. I2c not correct"""
        data = self.i2c.read_byte_data(self.address, 0xD0)
        print(data)

    def _readU16(self, reg):
        """Reads an unsigned 16 bit value van i2c"""
        result = self.i2c.read_word_data(self.address, reg)
        return result

    def _readS16(self, reg):
        """Reads a signed 16 bit value van i2c"""
        result = self._readU16(reg)
        if result > 32767:
            result -= 65536
        return result

    def _load_calibration(self):
        self.cal_t1 = int(self._readU16(BMP280_DIG_T1))  # UINT16
        self.cal_t2 = int(self._readS16(BMP280_DIG_T2))  # INT16
        self.cal_t3 = int(self._readS16(BMP280_DIG_T3))  # INT16
        self.cal_p1 = int(self._readU16(BMP280_DIG_P1))  # UINT16
        self.cal_p2 = int(self._readS16(BMP280_DIG_P2))  # INT16
        self.cal_p3 = int(self._readS16(BMP280_DIG_P3))  # INT16
        self.cal_p4 = int(self._readS16(BMP280_DIG_P4))  # INT16
        self.cal_p5 = int(self._readS16(BMP280_DIG_P5))  # INT16
        self.cal_p6 = int(self._readS16(BMP280_DIG_P6))  # INT16
        self.cal_p7 = int(self._readS16(BMP280_DIG_P7))  # INT16
        self.cal_p8 = int(self._readS16(BMP280_DIG_P8))  # INT16
        self.cal_p9 = int(self._readS16(BMP280_DIG_P9))  # INT16

    def read_raw_data(self, register):
        data = self.i2c.read_i2c_block_data(self.address, register, 3)
        data = self.convert_data(data[0], data[1], data[2])
        return data

    def _compensate_temp(self, raw_temp):
        t1 = (((raw_temp >> 3) - (self.cal_t1 << 1)) * (self.cal_t2) >> 11)
        t2 = (((((raw_temp >> 4) - (self.cal_t1)) * ((raw_temp >> 4) - (self.cal_t1))) >> 12) * (self.cal_t3)) >> 14
        return t1 + t2

    def read_temperature(self):
        raw_temp = self.read_raw_data(BMP280_TEMPDATA)
        compensated_temp = self._compensate_temp(raw_temp)
        temp = float(((compensated_temp * 5 + 128) >> 8)) / 100
        return temp

    def read_pressure(self):
        raw_temp = self.read_raw_data(BMP280_TEMPDATA)
        compensated_temp = self._compensate_temp(raw_temp)
        raw_pressure = self.read_raw_data(BMP280_PRESSUREDATA)

        p1 = compensated_temp - 128000
        p2 = p1 * p1 * self.cal_p6
        p2 += (p1 * self.cal_p5) << 17
        p2 += self.cal_p4 << 35
        p1 = ((p1 * p1 * self.cal_p3) >> 8) + ((p1 * self.cal_p2) << 12)
        p1 = ((1 << 47) + p1) * (self.cal_p1) >> 33

        if 0 == p1:
            return 0

        p = 1048576 - raw_pressure
        p = (((p << 31) - p2) * 3125) / p1
        p1 = (self.cal_p9 * (int(p) >> 13) * (int(p) >> 13)) >> 25
        p2 = int((self.cal_p8 * p)) >> 19
        p = (int((p + p1 + p2)) >> 8) + ((self.cal_p7) << 4)

        return float(p / 256)

    def read_altitude(self, sealevel_pa=101325.0):
        """Calculates the altitude in meters."""
        # Calculation taken straight from section 3.6 of the datasheet.
        pressure = float(self.read_pressure())
        altitude = 44330.0 * (1.0 - pow(pressure / sealevel_pa, (1.0 / 5.255)))
        return altitude

    def read_sealevel_pressure(self, altitude_m=0.0):
        """Calculates the pressure at sealevel when given a known altitude in
        meters. Returns a value in Pascals."""
        pressure = float(self.read_pressure())
        p0 = pressure / pow(1.0 - altitude_m / 44330.0, 5.255)
        return p0

    @staticmethod
    def convert_data(msb, lsb, xlsb):
        data = ((msb << 8 | lsb) << 8 | xlsb) >> 4
        return data

def main():
    try:
        barom = BMP280()
        print(barom.read_temperature())
        print(barom.read_pressure())
        print(barom.read_sealevel_pressure(20))
        print(barom.read_altitude(101679))
    except KeyboardInterrupt:
        pass
    finally:
        GPIO.cleanup()


if __name__ == '__main__':
    main()