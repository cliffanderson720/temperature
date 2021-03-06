# Read several temperature files and join into 1 df
import glob
import pandas as pd
import subprocess


FILE_GLOB = '2*_temp.csv'


def fetch_readings(host='raspberrypi', remote_dir='temperature', local_dir='./'):
    # fetch temperature readings from raspberrypi/arduino onto the local machine for analysis
    subprocess.run(['scp', f'{host}:{remote_dir}/{FILE_GLOB}', local_dir])


def concat_readings(glob_pattern=FILE_GLOB, write=True):
    """
    :param glob_pattern: shell glob pattern to identify the temperature readings to concatenate
    :param write: boolean about whether the combined df should be written to temp.csv
    :return: None
    """
    files = glob.glob(glob_pattern)
    dfs = [pd.read_csv(file) for file in files]
    df = pd.concat(dfs)
    if write:
        df.to_csv('temp.csv', index=False)
    return df


if __name__ == '__main__':
    fetch_readings()
    concat_readings()
