import csv
import sys
import os
import time
import yaml
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from thermocouple import Arduino


def get_POSIX_date():
    return time.strftime('%Y-%m-%d')

def get_POSIX_time():
    return time.strftime('%Y-%m-%d %H:%M')


TEMP_LOG = f'{get_POSIX_date()}_temp.csv'
HOURS_PER_S = 60 * 60


class Temperature:
    def __init__(self, params="params.yaml"):
        with open(params) as request_params:
            self.request_params = yaml.load(request_params, Loader=yaml.FullLoader)
        self.thermostat = float(input('What is the current thermostat setpoint? '))

    def get_weather(self):
        try:
            retry_strategy = Retry(total=5, backoff_factor=0.1)
            adapter = HTTPAdapter(max_retries=retry_strategy)
            http = requests.Session()
            http.mount('https://', adapter)

            response = http.request(
                'GET',
                'https://api.openweathermap.org/data/2.5/weather',
                params=self.request_params)

        except requests.exceptions.ConnectionError:
            raise Exception('You cannot connect right now. Retry your internet connection')

        if not response:
            print('Error querying OpenWeather API')
            sys.exit(response.status_code)
        return response.json()

    def compile_reading(self):
        json_response = self.get_weather()
        air = json_response['main']
        out = {k: air[k] for k in air.keys() if k in ['temp', 'humidity']}
        # make the weather temp more clear
        out['outside'] = out.pop('temp')
        
        wind = {k:json_response['wind'][k] for k in ('speed','deg')}
        out.update(wind)
        out.update({'time': get_POSIX_time(),
                    'thermo': Arduino().get_temp(),
                    'thermostat': self.thermostat,
                    })
        return out

    def write_line(self):
        reading = self.compile_reading()
        if not os.path.exists(TEMP_LOG):
            with open(TEMP_LOG, 'w') as new_log:
                writer = csv.DictWriter(new_log, fieldnames=reading.keys())
                writer.writeheader()
        with open(TEMP_LOG, 'a+', newline='') as write_obj:
            csv_writer = csv.DictWriter(write_obj, fieldnames=reading.keys())
            csv_writer.writerow(reading)


if __name__ == '__main__':
    temp = Temperature()
    while True:
        temp.write_line()
        time.sleep(0.25 * HOURS_PER_S)
