import collections
import matplotlib.pyplot as plt
import pickle


FILENAME = __file__.replace('.py', '.data')
OUT = __file__.replace('.py', '')


def is_target_action(action):
    # return action in ['click', 'clean', 'cleanAll']
    return action in ['click', 'clean']
    # return action in ['cleanAll']


def add_line(data, pkg):
    plt.plot(data, linestyle='-', linewidth=1.0, label=pkg)
    # if len(data) > 10:
    #     plt.plot(data, linestyle='-', linewidth=1.0, label=pkg)


class Device:
    def __init__(self, ):
        self.d = collections.defaultdict(list)
        self.raw = list()
        self.choice = 0
        self.notification_dict = set()

    def _update_status(self, json_obj):
        if json_obj['method'] == 'getMaybeAlternative':
            if json_obj['packageName'] == 'com.android.server.notification':
                if json_obj['label'] == 'sort':
                    if json_obj['status'] == 'success':
                        # if hasattr(self, 'notification_dict'):
                        #     print(self.notification_dict)
                        self.notification_dict = dict()
                        self.choice = json_obj['choice']
    # Maybe-Service-PhoneLab: {"Action":"life_cycle","method":"getMaybeAlternative","packageName":"com.android.server.notification","label":"sort","status":"success","choice":0,"timestamp":1448642448706,"uptimeNanos":59891102612815,"LogFormat":"1.1"}

    def _update_json(self, json_obj):
        json_obj['choice'] = self.choice
        return json_obj

    def add(self, json_obj, tag):
        self.raw.append((tag, json_obj))

    def add_compare(self, json_obj):
        status = json_obj['status']
        if status == 'success' or status == 'equal':
            left_pkg = json_obj['leftPkg']
            right_pkg = json_obj['rightPkg']
            l_score = json_obj['lScore']
            r_score = json_obj['rScore']
            self.notification_dict[left_pkg] = l_score
            self.notification_dict[right_pkg] = r_score
            pass
        elif status == 'abort':
            left_pkg = json_obj['leftPkg']
            pass
        elif status == 'cancel':
            pass
        else:
            print('this could never happen', json_obj)
        pass

    def one_json(self, tag, json_obj):
        action = json_obj['Action']
        if is_target_action(action):
            pkg = json_obj['package']
            self._update_json(json_obj)
            self.d[pkg].append(json_obj)
            notification_list = sorted(self.notification_dict.items(), key=lambda x: x[1], reverse=True)
            array = [i for i, (pkg_name, score) in enumerate(notification_list) if pkg_name == pkg]
            print(array)
        elif action == 'cleanAll':
            clean_list = json_obj['cleaned']
            for i in clean_list:
                i['timestamp'] = json_obj['timestamp']
                i['Action'] = json_obj['Action']
                pkg = i['package']
                self._update_json(i)
                self.d[pkg].append(i)
        elif action == 'compare':
            self.add_compare(json_obj)
        elif action == 'life_cycle':
            self._update_status(json_obj)

    def process(self, device_id):
        print(device_id)
        for tag, json_obj in self.raw:
            self.one_json(tag, json_obj)
        pass

    def draw(self, device_id):
        plt.clf()
        if len(self.d) is 0:
            return
        x_limit = 0
        for (pkg, records) in self.d.items():
            record_list = sorted(records, key=lambda x: x['timestamp'])
            # print(pkg)
            # print([(i['score'], i['Action']) for i in record_list])
            x_limit = max(x_limit, len(record_list))
            add_line([i['score'] for i in record_list], pkg)
        # print(len(d))
        plt.legend(loc='upper right', shadow=True, prop={'size': 6})
        plt.ylim([-0.5, 1.5])
        plt.xlim([0, x_limit + 100])
        plt.savefig(OUT + '/' + device_id + '.pdf', dpi=200)
        # plt.show()


class Log:
    def __init__(self, loader):
        self.loader = loader

    def process(self):
        # lines = self.loader.get_generator(['Power-Battery-PhoneLab', 'Network-Telephony-PhoneLab'])
        # lines = self.loader.get_generator(['Maybe-Notification-PhoneLab', 'Network-Telephony-PhoneLab'])
        lines = self.loader.get_generator(['Maybe-Notification-PhoneLab', 'Maybe-Service-PhoneLab'])
        device_dict = collections.defaultdict(Device)
        for tag, json, tokens in lines:
            # print(tag, json, tokens[0])
            device_id = tokens[0]
            pre = len(device_dict)
            # if pre > 2:
            #     break
            device = device_dict[device_id]
            if pre != len(device_dict):
                print(device_id)
            device.add(json, tag)
            # if json['Action'] == 'android.intent.action.SIG_STR':
            #     print(json)
            pass
        # for device_id, device in device_dict.items():
        #     device.draw(device_id)
        pickle.dump(device_dict, open(FILENAME, 'wb'))

if __name__ == '__main__':
    d = pickle.load(open(FILENAME, 'rb'))
    for key, dev in d.items():
        # print(key)
        dev.process(key)
        # dev.draw(key)

# d = dict()
# d['a'] = 1
# d['b'] = 2
# pickle.dump(d, open('tmp.data', 'wb'))
