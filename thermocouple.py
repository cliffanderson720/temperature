#!/usr/bin/env python3
import serial
import os


class Arduino:
    def __init__(self):
        # Find where the arduino is located between ttyUSB0 or ttyUSB1
        my_tty = '/dev/ttyUSB0'
        if not os.path.exists(my_tty):
            my_tty = '/dev/ttyUSB1'
        self.connection = serial.Serial(my_tty, 9600, timeout=1.1)
        self.connection.flushInput()

    def get_temp(self, readings=5):
        temps = []
        try:
            for i in range(readings):
                try:
                    line = self.connection.readline().decode('utf-8').strip()
                except UnicodeDecodeError as UDE:
                    print(UDE)
                    self.connection.flushInput()
                    continue
                if i > 1:
                    temps.append(float(line))
        except KeyboardInterrupt:
            return temps
        temp = round(sum(temps)/len(temps), 2)
        print(f'Arduino temperature: {temp} degF')
        return temp


if __name__ == '__main__':
    Arduino().get_temp()
