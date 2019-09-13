import json
class key_version:
    def __init__(self, d = None):
        if d == None:
            self.data = {}
        else:
            self.data = d
    def get_version(self, key):
        if not key in self.data:
            return 0
        return self.data[key][0]
    def get_timestamp(self, key):
        if not key in self.data:
            return 0
        return self.data[key][1]
    def get_tombstone(self, key):
        if not key in self.data:
            return True
        return self.data[key][2]
    def get_all(self, key):
        return self.data[key]
    def incr(self, key, timestamp):
        if not key in self.data:
            self.data[key] = [1, timestamp, False]
        else:
            curr = self.data[key][0]
            self.data[key] = [curr+1, timestamp, self.data[key][2]]
    def set(self, key, version, timestamp, tombstone):
        self.data[key] = [version, timestamp, tombstone]
    def __str__(self):
        return json.dumps(self.data)
    
    def copy(self):
        return key_version(self.data.copy())
    @classmethod
    def from_string(cls, string):
        if string == '':
            return key_version()
        obj = json.loads(string)
        return key_version(obj)


    # # Compares two key version mappings as defined in class - a vector clock self is less than another vector
    # # clock other if all its keys exist in other, all the values of those keys in other are greater than or equal to this vector clock, and at least one is more than self
    # # Returns true, false, or none
    # def __lt__(self, other):
    #     if not self.data.keys().issubset(other.data.keys()):
    #         return None #incomparable
    #     # check all keys in other are >= the keys in self
    #     for key in self.data.keys():
    #         if self.data[key] > other.data[key]:
    #             return False
    #     # check at least one key in other is strictly >  that key in self
    #     for key in self.data.keys():
    #         if self.data[key] < other.data[key]:
    #             return True
    #     return False