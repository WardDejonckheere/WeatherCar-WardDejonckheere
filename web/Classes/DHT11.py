from RPi import GPIO
import time
from collections import namedtuple
from statistics import mean

GPIO.setmode(GPIO.BCM)

Data = namedtuple("DHT11", "TEMP_CEL HUMIDITY_PERC")

class DHT11:
    def __init__(self, pin):
        self.pin = pin

    def get_result(self, max_tries=2):
        """Tries to get te result multiple times (max_tries)"""
        for try_num in range(0, max_tries):
            try:
                data = self.get_result_once()
                return Data(data[0], data[1])
            except Exception:
                time.sleep(1)

    def get_result_once(self):
        """Tries to get the result once"""
        byte_array = self._get_bytes_from_dht()

        checksum = byte_array[0] + byte_array[1] + \
                   byte_array[2] + byte_array[3] & 255  #
        if checksum != byte_array[4]:
            raise Exception('Checksum error')

        rel_humidity = byte_array[0]
        temp = byte_array[2]
        return temp, rel_humidity

    def _get_bytes_from_dht(self):
        """Contact DHT and return bytes"""
        raw_bits = []
        try:
            GPIO.setup(self.pin, GPIO.OUT)

            # Pull down for 20ms
            GPIO.output(self.pin, GPIO.LOW)
            time.sleep(20 / 1000.0)

            GPIO.output(self.pin, GPIO.HIGH)

            GPIO.setup(self.pin, GPIO.IN)
            # GPIO.setup(self.pin, GPIO.IN, GPIO.PUD_UP)
            raw_bits = self._collect_raw_bits()
        except Exception:
            GPIO.cleanup()

        impulses = self._get_data_impulses(raw_bits)
        if len(impulses) != 40:
            raise Exception('Missing data. Only got %d bits.' % len(impulses))

        bits = self._get_bits_from_impulses(impulses)
        return self._get_bytes_from_bits(bits)

    def _collect_raw_bits(self):
        seq_count = 0  # Sequential bits count
        last_bit = -1
        bits = []
        while seq_count < 64:
            bit = GPIO.input(self.pin)
            bits.append(bit)
            if last_bit != bit:
                seq_count = 0
                last_bit = bit
            else:
                seq_count += 1
        return bits

    def _get_bits_from_impulses(self, impulses):
        avg = mean(impulses)
        bits = []
        for impulse_length in impulses:
            bits.append(1 if impulse_length > avg else 0)
        return bits

    def _get_data_impulses(self, data_bits):
        impulses = []  # Defines length of each data impulse
        while len(data_bits) > 1:
            # Ignore pull down
            length = self._get_length_of_sequential_bits(data_bits, 0)
            data_bits = data_bits[length:]

            length = self._get_length_of_sequential_bits(data_bits, 1)
            data_bits = data_bits[length:]
            # Save length of pull up
            impulses.append(length)
        # Ignore init and final pull ups
        return impulses[1:-1]

    def _get_length_of_sequential_bits(self, bits, bit_type):
        for i, bit in enumerate(bits):
            if bit != bit_type:
                break
        return i

    def _get_bytes_from_bits(self, bits):
        byte_array = []
        for byte_index in range(0, len(bits), 8):
            byte = 0
            for bit_index in range(0, 8):
                byte = byte << 1 | bits[byte_index + bit_index]
            byte_array.append(byte)
        return byte_array

    def _get_temp_humidity_tuple(self, byte_array):
        rel_humidity = byte_array[0]
        temp = byte_array[2]
        return temp, rel_humidity

def main():
    try:
        dht11 = DHT11(17)
        print(dht11.get_result())
    except KeyboardInterrupt:
        pass
    finally:
        GPIO.cleanup()


if __name__ == '__main__':
    main()