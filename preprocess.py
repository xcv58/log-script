#!/usr/bin/env python3
import gzip
import os

import click
from loader import LogLoader


def log_key(line):
    tokens = line.split()
    try:
        res = [int(i) for i in tokens[2].split('.')]
        return res
    except ValueError as e:
        print(line)
        print(e)
    return [0, 0]


def remove_dup(content, device_id):
    lines = [i for i in content if device_id in i]
    lines = sorted(lines, key=log_key)
    pre = ''
    result = []
    for i in lines:
        if pre != i:
            result.append(i)
            pre = i
    total, valid, actual = len(content), len(lines), len(result)
    if actual > 0:
        crash = (total - valid) / valid
        print(total, valid, actual)
        print('dup: {:.2f}%'.format(1-actual/valid), 'crash: {:.5f}%'.format(crash))
    return result


class Device:
    def __init__(self, directory, pattern, output='./log', ext='.gz'):
        self.directory = directory
        self.pattern = pattern
        self.output = output
        self.ext = ext

    def process(self, device_id):
        # if os.path.isfile(os.path.join(self.output, device_id + self.ext)):
        #     print('skip')
        #     return
        loader = LogLoader(self.directory, self.pattern)
        content = [i for i in loader.get_all()]
        filter_content = remove_dup(content, device_id)
        if len(filter_content):
            f = gzip.open(os.path.join(self.output, device_id + self.ext), 'wt', compresslevel=1)
            for i in filter_content:
                f.write(i)
            f.close()
        pass


@click.command()
@click.option('--directory', '-d', help='The root directory of log files')
@click.option('--pattern', '-f', default='*.out', help='The filename pattern for log file')
@click.option('-c', help='The filename pattern for log file')
def process(directory, pattern, c):
    click.echo('process %s %s' % (directory, pattern))
    d = dict()
    for sub_folder in os.listdir(directory):
        if sub_folder != 'log':
            d[sub_folder] = Device(os.path.join(directory, sub_folder), pattern, output=os.path.join(directory, 'log'))
    for device_id, dev in sorted(d.items()):
        print(device_id)
        dev.process(device_id)
    return


if __name__ == '__main__':
    process()
