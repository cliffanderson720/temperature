import csv
import sys
import os
import time
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from thermocouple import Arduino


TEMP_LOG = 'temp.csv'


def get_weather():
    try:
        retry_strategy = Retry(total=5, backoff_factor=1)
        adapter = HTTPAdapter(max_retries=retry_strategy)
        http = requests.Session()
        http.mount('https://', adapter)
        response = http.request(
                'GET',
                'https://api.openweathermap.org/data/2.5/weather',
                 params={'q': 'Pittsburgh',
                        'APPID': '6ec427d33d4c26b4a5ba0a8ec4a51698',
                        'units': 'imperial'})

    except requests.exceptions.ConnectionError:
        raise Exception('You cannot connect right now. Retry your internet connection')

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
