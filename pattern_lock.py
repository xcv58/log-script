import collections
import pickle
import scipy.stats
from matplotlib import pyplot as plt
from sklearn import tree
from sklearn import svm
from sklearn.naive_bayes import GaussianNB
from sklearn.ensemble import RandomForestClassifier
from sklearn.ensemble import ExtraTreesClassifier
from sklearn import cross_validation
from sklearn.neighbors.nearest_centroid import NearestCentroid
from sklearn.cross_validation import StratifiedKFold
from sklearn.externals.six import StringIO

FILENAME = __file__.replace('.py', '.data')

TRAIN_SIZE = 60


def max_min(array):
    if array:
        return max(array), min(array)
    return 0, 0


def get_success_fail_rate(json_list):
    s = sum(1 for obj in json_list if obj['status'] == 'success')
    f = sum(1 for obj in json_list if obj['status'] == 'fail')
    rate = s / (s + f) if s + f > 0 else 0
    return s, f, rate


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

    def draw(self, device_id, train_length):
        result = dict()
        # print(self.info)
        success_unlock_size = []
        fail_unlock_size = []
        for hit_factor, json_list in self.d.items():
            s, f, rate = get_success_fail_rate(json_list)
            s_train, f_train, rate_train = get_success_fail_rate(json_list[:train_length])
            result[hit_factor] = (rate, rate_train)

            # s = sum(1 for obj in json_list if obj['status'] == 'success')
            # f = sum(1 for obj in json_list if obj['status'] == 'fail')
            pattern_size_key = 'patternSize'
            success_unlock_size += [obj[pattern_size_key] for obj in json_list if obj['status'] == 'success']
            fail_unlock_size += [obj[pattern_size_key] for obj in json_list if obj['status'] == 'fail']
            # print('success', [obj[pattern_size_key] for obj in json_list if obj['status'] == 'success'])
            # print('fail', [obj[pattern_size_key] for obj in json_list if obj['status'] == 'fail'])
            # print("{}\t{:.2f}".format(hit_factor, s/(s+f)), len(json_list), s, f)
            # for key, items in itertools.groupby(sorted(json_list, key=lambda x: x['status']), lambda x: x['status']):
            #     print(key, sum(1 for i in items))
            # for obj in json_list:
            #     print(obj['status'], obj['patternSize'])

        s_max, s_min = max_min(success_unlock_size)
        f_max, f_min = max_min(fail_unlock_size)
        feature = (f_max, f_min, s_max, s_min)
        return [result, self.info, feature]


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


def calculate_correlation(data, feature_name):
    # print('correlation')
    labels = [i[-1] for i in data]
    values = []
    for index in range(5, len(data[0])):
        label = feature_name[index]
        feature = [i[index] for i in data]
        correlation, p_value = scipy.stats.pearsonr(feature, labels)
        # print(index, '{:.3f}\t{:.5f}'.format(correlation, p_value), label, sep='\t')
        values.append((correlation, label))
    return values


def plot_tree(X, Y, feature_name, clf):
    clf = clf.fit(X, Y)
    with open('test.dot', 'w') as f:
        tree.export_graphviz(
            clf,
            out_file=f,
            feature_names=feature_name[:-1]
        )
    pass


def ml(matrix, feature_name, clf, name=None):
    # matrix.sort(key=lambda x: x[-1])
    X = [i[:-1] for i in matrix]
    Y = [int(i[-1] * 10) for i in matrix]
    cv = cross_validation.StratifiedKFold(Y, n_folds=2, shuffle=True, random_state=0)
    scores = cross_validation.cross_val_score(
        clf,
        X, Y,
        cv=cv
    )
    # print(scores, scores.mean(), scores.std())
    if name == 'Decision Tree':
        plot_tree(X, Y, feature_name, clf)
    return scores.mean(), scores.std()
    pass


def process(d, train_length):
    res = []
    total_device = len(d)
    valid = 0
    total_info = 0
    total_both = 0
    matrix = []
    for device_id, dev in d.items():
        success_dict, info, (f_max, f_min, s_max, s_min) = dev.draw(device_id, train_length)

        gender = info.get('phonelab_gender', '?')
        age = info.get('phonelab_age', '?')
        desktop = info.get('phonelab_desktop', '?')
        laptop = info.get('phonelab_laptop', '?')
        another_phone = info.get('phonelab_another_phone', '?')

        if gender != '?' or age != '?' or desktop != '?' or laptop != '?' or another_phone != '?':
            total_info += 1

        if success_dict:
            target_class = max(success_dict.items(), key=lambda x: x[1][0])[0]
            target_class_train = max(success_dict.items(), key=lambda x: x[1][1])[0]
            if gender != '?' or age != '?' or desktop != '?' or laptop != '?' or another_phone != '?':
                total_both += 1
            valid += 1
            # print(key)
            rate_4, rate_4_train = success_dict.get(0.4, (0, 0))
            rate_6, rate_6_train = success_dict.get(0.6, (0, 0))
            rate_8, rate_8_train = success_dict.get(0.8, (0, 0))
            rate_1, rate_1_train = success_dict.get(1.0, (0, 0))
            # print(gender, age, desktop, laptop, another_phone,
            #       f_min, f_max, s_min, s_max,
            #       rate_4_train, rate_6_train, rate_8_train, rate_1_train,
            #       target_class_train,
            #       rate_4, rate_6, rate_8, rate_1,
            #       target_class,
            #       sep='\t')
            vector = (
                # gender, age, desktop, laptop, another_phone,
                f_min, f_max,
                s_min, s_max,
                rate_4_train,
                rate_6_train,
                rate_8_train,
                rate_1_train,
                target_class_train,
                # rate_4, rate_6, rate_8, rate_1,
                target_class
            )
            matrix.append(vector)
            res += [success_dict]
            pass
        pass
    feature_name = (
        # 'gender', 'age', 'desktop', 'laptop', 'another_phone',
        'f_min', 'f_max',
        's_min', 's_max',
        'rate_4_train',
        'rate_6_train',
        'rate_8_train',
        'rate_1_train',
        'target_class_train',
        # 'rate_4', 'rate_6', 'rate_8', 'rate_1',
        'target_class'
    )
    # values = calculate_correlation(matrix, feature_name)
    # return values
    print(collections.Counter([i[-1] for i in matrix]))

    # clf = svm.LinearSVC()
    # clf = GaussianNB()
    # clf = tree.DecisionTreeClassifier()
    results = []
    for i in range(50):
        clf_list = list()
        clf_list += [('SVM', svm.SVC())]
        clf_list += [('Decision Tree', tree.DecisionTreeClassifier())]
        clf_list += [('Naive Bayes', GaussianNB())]
        clf_list += [('Nearest Centroid', NearestCentroid())]
        clf_list += [('Random Forest', RandomForestClassifier())]
        clf_list += [('Extra Tree', ExtraTreesClassifier())]
        legend = [name for name, _ in clf_list]
        vector = []
        for name, clf in clf_list:
            mean, std = ml(matrix, feature_name, clf, name)
            # print(name)
            # print('{:.2f}\t{:.3f}'.format(mean, std))
            vector.append((mean, std))
        results.append(vector)

    print(len(results))
    results = list(zip(*results))
    for i, label in zip(results, legend):
        print(label,
              sum([j[0] for j in i]) / len(i))
        print(sorted(['{:.4f}'.format(j[0]) for j in i]))

    # class_labels = [max(i.items(), key=lambda x: x[1][0])[0] for i in res]
    # print(collections.Counter(class_labels))
    # print(collections.Counter([max(i.items(), key=lambda x: x[1][1])[0] for i in res]))
    print(valid, total_info, total_both, total_device, valid / total_device)


if __name__ == '__main__':
    loaded_data = pickle.load(open(FILENAME, 'rb'))
    process(loaded_data, 30)
    # x = range(10, 100, 1)
    # y = []
    # for i in x:
    #     # print('train_length', i)
    #     y.append(process(loaded_data, i))
    # labels = [i[1] for i in y[0]]
    # print(labels)
    # for i in range(len(labels)):
    #     nums = [j[i][0] for j in y]
    #     c_max, c_min = max_min(nums)
    #     limit = 0.3
    #     if abs(c_max) > limit or abs(c_min) > limit:
    #         plt.plot(x, nums, label=labels[i], linewidth=1.0)
    # # plt.plot(x, y)
    # plt.legend()
    # plt.legend(loc='upper right', prop={'size': 9})
    # plt.ylim((-1.2, 1.2))
    # plt.show()
