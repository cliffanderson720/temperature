import requests
import csv
import sys
import os
import time
from thermocouple import Arduino


TEMP_LOG = 'temp.csv'


def get_weather():
    response = requests.get(
        'https://api.openweathermap.org/data/2.5/weather',
        params={'q': 'Pittsburgh',
                'APPID': '6ec427d33d4c26b4a5ba0a8ec4a51698',
                'units': 'imperial'})
    if not response:
        print('Failed')
        sys.exit(response.status_code)
    json_response = response.json()
    return json_response


def get_time():
    return time.strftime('%Y-%m-%d %H:%M')


def compile_reading():
    json_response = get_weather()
    air = json_response['main']
    out = {k: air[k] for k in air.keys() if k in ['temp', 'humidity']}
    out.update(**json_response['wind'])
    out.update({'time': get_time(),
                'thermo': Arduino().get_temp()})
    return out


def write_line(reading):
    if not os.path.exists(TEMP_LOG):
        with open(TEMP_LOG, 'w') as new_log:
            writer = csv.DictWriter(new_log, fieldnames=reading.keys())
            writer.writeheader()
    with open(TEMP_LOG, 'a+', newline='') as write_obj:
        csv_writer = csv.DictWriter(write_obj, fieldnames=reading.keys())
        csv_writer.writerow(reading)


if __name__ == '__main__':
    reading = compile_reading()
    write_line(reading)
