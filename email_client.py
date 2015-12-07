import collections
import pickle

import sys

import itertools

FILENAME = __file__.replace('.py', '.data')


class Message:
    def __init__(self, account_id, uid, message_id, timestamp, sync_count, sync_interval=-1):
        self.account_id = account_id
        self.uid = uid
        self.message_id = message_id
        self.timestamp = timestamp
        self.sync_count = sync_count
        self.sync_interval = sync_interval

    def get_str(self):
        return '{account_id}-{uid}-{message_id}'.format(
            account_id=self.account_id,
            uid=self.uid,
            message_id=self.message_id)


class Device:
    def __init__(self):
        self.d = collections.defaultdict(list)
        self.json_list = list()
        self.info = {}

    def add(self, json_obj):
        if json_obj['Action'] == 'personal_information':
            self.info = json_obj
        else:
            self.json_list.append(json_obj)
        pass

    def get_pairs(self, device_id):
        key_unsync_result = 'unsyncResult'
        sync_count_dict = dict()
        d = dict()
        # print(self.info)

        result = []
        interact_message_set = set()
        self.json_list.sort(key=lambda x: x['timestamp'])
        sync_interval = -1
        for obj in self.json_list:
            if obj['Action'] == 'sync' and not obj['upload'] and not obj['uiRefresh']:
                sync_interval = obj['syncs'][0]['oldSyncInterval']
                account_id = obj['accountId']
                sync_count_dict[account_id] = sync_count_dict.get(account_id, 0) + 1
                sync_count = sync_count_dict[account_id]
                sync_results = obj['syncResults']
                if len(sync_results) == 1:
                    res = sync_results[0]
                    timestamp = obj['timestamp']
                    if key_unsync_result in res:
                        # print(res[key])
                        for message in res[key_unsync_result]:
                            uid = message['uid']
                            message_id = message['messageId']
                            # print('get', device_id, timestamp, account_id, uid, message_id, sync_count)
                            message_obj = Message(account_id, uid, message_id, timestamp, sync_count, sync_interval)
                            key = message_obj.get_str()
                            if key in d:
                                if timestamp == d[key].timestamp:
                                    # print(key, 'already exists!')
                                    # print(timestamp, d[key].timestamp)
                                    pass
                            d[key] = message_obj
                    pass
            elif obj['Action'] == 'update':
                account_id = obj['accountId']
                timestamp = obj['timestamp']
                uid = obj['uid']
                message_id = obj['messageId']
                sync_count = sync_count_dict.get(account_id, 0)
                tmp = Message(account_id, uid, message_id, timestamp, sync_count, sync_interval)
                key = tmp.get_str()
                if key in interact_message_set:
                    pass
                interact_message_set.add(key)
                if key in d:
                    obj = d[key]
                    # print(obj.sync_count, sync_count, obj.sync_interval, (timestamp-obj.timestamp)/1000)
                    result.append((obj, tmp))
                # else:
                #     print(key, 'not in d')
                # print('update', device_id, timestamp, account_id, uid, message_id)
        return result

    def get_feature_dict(self, device_id):
        results = self.get_pairs(device_id)
        if results:
            print(device_id, len(self.json_list))
            for receive, interact in results:
                old_sync_count = receive.sync_count
                new_sync_count = interact.sync_count
                old_time = receive.timestamp
                new_time = interact.timestamp
                interval = (new_time - old_time) / 1000
                # print(new_sync_count,
                #       interact.sync_interval,
                #       receive.sync_interval,
                #       # old_sync_count, new_sync_count,
                #       new_sync_count - old_sync_count,
                #       interval, interact.get_str(),
                #       sep='\t')
                # print(receive.sync_interval, new_sync_count - old_sync_count, k)

            sessions = []
            group_data = itertools.groupby(results, key=lambda x: (x[1].sync_count, x[1].account_id))
            for k, items in group_data:
                # receive, interact = max(items, key=lambda x: x[0].timestamp)
                # old_sync_count = receive.sync_count
                # new_sync_count = interact.sync_count
                # old_time = receive.timestamp
                # new_time = interact.timestamp
                # interval = (new_time - old_time) / 100
                # print(new_sync_count, receive.sync_interval, old_sync_count, new_sync_count,
                #       new_sync_count - old_sync_count,
                #       interval, interact.get_str())
                # print(receive.sync_interval, new_sync_count - old_sync_count, k)
                array = []
                for receive, interact in items:
                    old_sync_count = receive.sync_count
                    new_sync_count = interact.sync_count
                    old_time = receive.timestamp
                    new_time = interact.timestamp
                    interval = (new_time - old_time) / 100
                    array += [(new_sync_count - old_sync_count, interact.sync_interval, new_time, (new_time-old_time)/1000)]
                    # print(new_sync_count, receive.sync_interval, old_sync_count, new_sync_count,
                    #       new_sync_count - old_sync_count,
                    #       interval, interact.get_str())
                # print(k)
                # for interval, sync_interval, time, time_sec in sorted(array, key=lambda x: (x[2], x[0])):
                #     # print(interval, sync_interval, time, time_sec)
                #     pass
                tmp = sorted(array, key=lambda x: x[2])
                # print([(i[2] - j[2]) / 1000 for i, j in zip(tmp[1:], tmp[:-1])])
                # print(min(array, key=lambda x: (x[0], x[2])))
                sessions.append(min(array, key=lambda x: (x[0], x[2])))
                # print('')
                # for receive, interact in results:
                #     old_sync_count = receive.sync_count
                #     new_sync_count = interact.sync_count
                #     old_time = receive.timestamp
                #     new_time = interact.timestamp
                #     interval = (new_time - old_time) / 100
                #     print(new_sync_count, receive.sync_interval, old_sync_count, new_sync_count,
                #           new_sync_count - old_sync_count,
                #           interval, interact.get_str())
                # print(obj.sync_count, sync_count, obj.sync_interval, (timestamp-obj.timestamp)/1000)
                pass
            for key, items in itertools.groupby(sorted(sessions, key=lambda x: x[1]), key=lambda x: x[1]):
                items = [i for i in items]
                intervals = [i[0] for i in items]
                times = [i[3] for i in items]
                mean_interval = sum(intervals) / len(intervals)
                weight_mean = sum([min(3, i) for i in intervals]) / len(intervals)
                mean = sum(times) / len(times)
                print(key, intervals)
                # print(key, '{:.2f}\t{:.2f}\t{:7.2f}'.format(mean_interval, weight_mean, mean), sep='\t')
                # print(key, '{:.2f}'.format(mean_interval, weight_mean, mean), sep='\t')
            print(len(sessions))
            # print(sessions)



class Log:
    def __init__(self, loader):
        self.loader = loader

    def process(self):
        lines = self.loader.get_generator(['Maybe-Email-PhoneLab', 'Maybe-Service-PhoneLab.*personal_information'])
        device_dict = collections.defaultdict(Device)
        s = set()
        for tag, json_obj, tokens in lines:
            device_id = tokens[0]

            pre = len(device_dict)

            device = device_dict[device_id]
            if pre != len(device_dict):
                print(device_id)

            device.add(json_obj)
            # print(tag, json)
            s.add(json_obj['Action'])
            # if json_obj['Action'] == 'android.intent.action.SIG_STR':
            #     print(json)
            pass
        pickle.dump(device_dict, open(FILENAME, 'wb'))
        print(s)

if __name__ == '__main__':
    d = pickle.load(open(FILENAME, 'rb'))

    for device_id, dev in sorted(d.items()):
        dev.get_feature_dict(device_id)
        # results = dev.get_pairs(device_id)

