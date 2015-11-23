import os
import sys
import json

if len(sys.argv) == 1:
    print('no argument')
    sys.exit()

filename = sys.argv[1]

if not os.path.isfile(filename):
    print('%s is not a file' % filename)
    sys.exit()

f = open(filename, 'r')
result = []
for i in f:
    if 'Maybe-Service-PhoneLab: {"Action":"query_backend"' in i:
        index = i.find('{')
        result.append(json.loads(i[index:]))

print('query time', [i['end'] - i['start'] if 'suc' in i['status'] else -1 for i in result],
      len([i['end'] - i['start'] if 'suc' in i['status'] else -1 for i in result]))
interval = [(i['start'] - j ['start']) for i, j in zip(result[1:], result[:-1])]
print('interval', [i / 1000 for i in interval])
short = [i for i in interval if abs(i) < 3000]
print('interval less than 3 sec', short)
print(len(short), len(interval))
