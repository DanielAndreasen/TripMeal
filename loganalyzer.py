import numpy as np
import matplotlib.pyplot as plt
import matplotlib
from datetime import datetime
plt.style.use('ggplot')

def log_converter(line, logdict):
    line = line.split(' ')
    if not line[1].startswith('heroku[router]'):
        return False

    timestamp = line[0]
    logdict[timestamp] = {}
    for ll in line[2::]:
        ll = ll.split('=')
        logdict[timestamp][ll[0]] = ll[1]


def get_data(dict, key):
    n = len(dict)
    data = np.zeros(n)
    for i, date in enumerate(dict.keys()):
        if key in ['bytes', 'status']:
            data[i] = float(dict[date][key])
        elif key in ['service', 'connect']:
            data[i] = float(dict[date][key][:-2])
        else:
            pass
    return data


def convert_time(stamp):
    stamp = stamp[:-6].replace('T', ' ')
    return datetime.strptime(stamp, '%Y-%m-%d %H:%M:%S.%f')


if __name__ == '__main__':
    logdict = {}
    with open('logfile.txt', 'r') as lines:
        for i, line in enumerate(lines):
            log_converter(line, logdict)


    for date in logdict.keys():
        if 'register' in logdict[date]['path']:
            print date, 'PATH:', logdict[date]['path']

    bytes = get_data(logdict, 'bytes')
    service = get_data(logdict, 'service')
    status = get_data(logdict, 'status')
    connect = get_data(logdict, 'connect')
    dates = matplotlib.dates.date2num(map(convert_time, logdict.keys()))

    plt.subplot(211)
    plt.plot_date(dates, bytes, label='bytes')
    plt.plot_date(dates, status, label='status')
    plt.legend(frameon=False)
    plt.subplot(212)
    plt.plot_date(dates, service, label='service')
    plt.plot_date(dates, connect, label='connect')
    plt.xlabel('Time')
    plt.ylabel('ms')
    plt.legend(frameon=False)
    plt.show()
