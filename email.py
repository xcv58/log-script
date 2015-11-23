class Log:
    def __init__(self, loader):
        self.loader = loader

    def process(self):
        lines = self.loader.get_generator(['Power-Battery-PhoneLab', 'Network-Telephony-PhoneLab'])
        for tag, json in lines:
            # print(tag, json)
            pass
