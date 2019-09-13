import json
class view_version:
    def __init__(self, d=None):
        if d == None:
            self.data = {}
        else:
            self.data = d

    def get_timestamp(self, key):
        if not key in self.data:
            return 0
        return self.data[key][1]
    def get_state(self, key):
        if not key in self.data:
            return True
        return self.data[key][0]
    def get_viewString(self):
        ips = []
        for ip in self.data:
            if self.data[ip][0] is True:
                ips.append(ip)
        return ",".join(ips)

    def get_key_list(self):
        return self.data.keys()

    def set(self, ip, state, timestamp):
        self.data[ip] = [state, timestamp]

    #remove self from viewlist for gossip
    def gossip_view(self, self_ip):
        gv = {}
        for key, value in self.data.items():
            if key != self_ip:
                gv[key] = value
            elif self.data[key][0] is False:
                gv[key] = value
        return json.dumps(gv)



    def __len__(self):
        return len(self.data)

    def __str__(self):
        return json.dumps(self.data)
    @classmethod
    def from_string(cls, string):
        if string == "":
            return view_version()
        obj = json.loads(string)
        return view_version(obj)
