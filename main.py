import csv
import sys
import os
import time
import yaml
import requests
import datetime
import itertools
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
    def __init__(self, params="params.yaml", setpoint_override=None):
        with open(params) as request_params:
            self.request_params = yaml.load(request_params, Loader=yaml.FullLoader)
        self.setpoint_schedule = self.request_params['setpoints']

        # Ask user for a setpoint schedule if none is given in the config. Allow manual override.
        self.setpoint = None
        if setpoint_override:
            self.setpoint = setpoint_override
            print(f'Using specified setpoint of {setpoint_override}')
        if not setpoint_override and not self.setpoint_schedule:
            self.setpoint = float(input('What is the current thermostat setpoint? '))

    def get_setpoint(self, setpoints):
        # if the setpoint setpoint has already been given, return it immediately 
        if self.setpoint:
            return self.setpoint

        # Else, figure it out from the schedule
        now = datetime.datetime.now()
        now = now.hour + now.minute / 60

        def time_in_range(start, end, x):
            """Return true if x is in the range [start, end]"""
            # https://stackoverflow.com/questions/10747974/how-to-check-if-the-current-time-is-in-range-in-python
            if start <= end:
                return start <= x <= end
            else:
                return start <= x or x <= end

        # build a list of times and setpoints from the yaml
        times = list(setpoints.keys())
        temps = list(setpoints.values())

        # make a cyclic iterator so we can check all contiguous pairs of times,
        # including wrapping from the latest around to the earliest time
        time_loop = itertools.cycle(times)
        temp_loop = itertools.cycle(temps)

        early_time = next(time_loop)
        for i in range(len(times) + 1):
            setpoint = next(temp_loop)

            # if the current time is later than the listed time, set the new temperature
            late_time = next(time_loop)
            if time_in_range(early_time, late_time, now):
                # return the setpoint when we find it
                return setpoint

            early_time = late_time

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
        clouds = json_response.get('clouds',0)
        if clouds:
            clouds = clouds.get('all',0)
        out.update({**wind,'clouds':clouds})
        out.update({'time': get_POSIX_time(),
                    'thermo': Arduino().get_temp(), # update this method to return na when the arduino isn't plugged in.
                    'setpoint': self.get_setpoint(self.setpoint_schedule),
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
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--setpoint_override', type=float, default=None,
                        help='Setpoint temperature of the heating system')
    args = parser.parse_args()

    temp = Temperature(setpoint_override = args.setpoint_override)
    while True:
        temp.write_line()
        time.sleep(150)
