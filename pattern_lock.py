import collections
import pickle

FILENAME = __file__.replace('.py', '.data')


def update_key(des, src, k, none):
    if src[k] != none:
        des[k] = src[k]


class Device:
    def __init__(self, ):
        self.d = collections.defaultdict(list)
        self.info = {}

    def update_info(self, json_obj):
        none = '<none>'
        update_key(self.info, json_obj, 'phonelab_desktop', none)
        update_key(self.info, json_obj, 'phonelab_laptop', none)
        update_key(self.info, json_obj, 'phonelab_another_phone', none)
        update_key(self.info, json_obj, 'phonelab_age', none)
        update_key(self.info, json_obj, 'phonelab_gender', none)

    def add(self, json_obj):
        if json_obj['Action'] == 'personal_information':
            self.update_info(json_obj)
            return
        hit_factor = json_obj['hitFactor']
        self.d[hit_factor].append(json_obj)

    def draw(self, device_id):
        result = dict()
        # print(self.info)
        for hit_factor, json_list in self.d.items():
            s = sum(1 for obj in json_list if obj['status'] == 'success')
            f = sum(1 for obj in json_list if obj['status'] == 'fail')
            # print("{}\t{:.2f}".format(hit_factor, s/(s+f)), len(json_list), s, f)
            result[hit_factor] = s/(s+f)
            # for key, items in itertools.groupby(sorted(json_list, key=lambda x: x['status']), lambda x: x['status']):
            #     print(key, sum(1 for i in items))
            # for obj in json_list:
            #     print(obj['status'], obj['patternSize'])
        return [result, self.info]


class Log:
    def __init__(self, loader):
        self.loader = loader

    def process(self):
        lines = self.loader.get_generator(['Maybe-Keyguard-PhoneLab', 'Maybe-Service-PhoneLab.*personal_information'])
        device_dict = collections.defaultdict(Device)
        for tag, json, tokens in lines:
            # print(tag, json, tokens[0])
            device_id = tokens[0]
            pre = len(device_dict)
            device = device_dict[device_id]
            if pre != len(device_dict):
                print(device_id)
            device.add(json)
            # if json['Action'] == 'android.intent.action.SIG_STR':
            #     print(json)
            pass
        # for device_id, device in device_dict.items():
        #     device.draw(device_id)
        pickle.dump(device_dict, open(FILENAME, 'wb'))


if __name__ == '__main__':
    d = pickle.load(open(FILENAME, 'rb'))
    res = []
    total_device = len(d)
    valid = 0
    total_info = 0
    total_both = 0
    for key, dev in d.items():
        success_dict, info = dev.draw(key)

        gender = info.get('phonelab_gender', '?')
        age = info.get('phonelab_age', '?')
        desktop = info.get('phonelab_desktop', '?')
        laptop = info.get('phonelab_laptop', '?')
        another_phone = info.get('phonelab_another_phone', '?')

        if gender != '?' or age != '?' or desktop != '?' or laptop != '?' or another_phone != '?':
            total_info += 1

        if success_dict:
            if gender != '?' or age != '?' or desktop != '?' or laptop != '?' or another_phone != '?':
                total_both += 1
            valid += 1
            # print(key)
            rate_4 = success_dict.get(0.4, '?')
            rate_6 = success_dict.get(0.6, '?')
            rate_8 = success_dict.get(0.8, '?')
            rate_1 = success_dict.get(1.0, '?')
            print(gender, age, desktop, laptop, another_phone, rate_4, rate_6, rate_8, rate_1)
            res += [success_dict]

    features = [sorted(i.items(), key=lambda x:x[1], reverse=True) for i in res]
    features = [i for i in features if i]
    print([i[0][0] for i in features])
    print(valid, total_info, total_both, total_device, valid/total_device)
