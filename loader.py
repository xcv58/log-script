import os
import fnmatch
import gzip
import bz2
import re
import json


def gen_concatenate(iterators):
    for it in iterators:
        yield from it


def gen_grep(pattern, line_list):
    pat = re.compile(pattern)
    for line in line_list:
        if pat.search(line):
            yield line


def gen_json(line_list):
    for line in line_list:
        index = line.find('{')
        level, tag = False, ''
        tokens = line.split()
        for i in tokens:
            if level:
                tag = i
                break
            if i in ['V', 'D', 'I', 'W', 'E']:
                level = True
        try:
            json_obj = json.loads(line[index:])
            yield (tag, json_obj, tokens)
        except json.decoder.JSONDecodeError as e:
            print(line, e)
            pass


def gen_opener(filename_list) -> GeneratorExit:
    """
    Open a sequence of files one at a time producing a file object.
    The file is closed immediately when proceeding to the next iteration.
    :param filename_list: filename list
    :yield: file object
    """
    for filename in filename_list:
        if filename.endswith('.gz'):
            f = gzip.open(filename, 'rt')
        elif filename.endswith('.bz2'):
            f = bz2.open(filename, 'rt')
        else:
            f = open(filename, 'rt')
        yield f
        f.close()


def gen_find(directory, pattern) -> GeneratorExit:
    for p, dir_list, file_list in os.walk(directory):
        for name in fnmatch.filter(file_list, pattern):
            yield os.path.join(p, name)


class LogLoader:
    def __init__(self, directory, filename_pattern):
        if not os.path.isdir(directory):
            raise Exception(directory + ' is not a valid path')
        self.directory = directory
        self.filename_pattern = filename_pattern

    def get_generator(self, tag_list=list(), pattern=''):
        filename = gen_find(self.directory, self.filename_pattern)
        files = gen_opener(filename)
        iterator = gen_concatenate(files)
        if not pattern:
            pattern = '|'.join(tag_list)
        grep_lines = gen_grep(pattern, iterator)
        return gen_json(grep_lines)

    def get_all(self):
        filename = gen_find(self.directory, self.filename_pattern)
        files = gen_opener(filename)
        iterator = gen_concatenate(files)
        return iterator

