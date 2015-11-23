#!/usr/bin/env python3

import click
from loader import LogLoader


def get_module(filename):
    return filename.split('.')[0]


@click.command()
@click.option('--directory', '-d', help='The root directory of log files')
@click.option('--pattern', '-f', default='*.out', help='The filename pattern for log file')
@click.option('-c', help='The filename pattern for log file')
def process(directory, pattern, c):
    click.echo('process %s %s' % (directory, pattern))
    module = __import__(get_module(c))
    class_ = getattr(module, 'Log')
    log_process = class_(LogLoader(directory, pattern))
    log_process.process()
    return

if __name__ == '__main__':
    process()

