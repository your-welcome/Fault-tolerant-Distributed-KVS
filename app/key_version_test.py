from key_version import key_version

# https://stackoverflow.com/questions/5998245/get-current-time-in-milliseconds-in-python
import time
current_milli_time = lambda: int(round(time.time() * 1000))

kv1 = key_version()
kv2 = key_version()


#write x=3
kv1.incr('x', current_milli_time())
payload = str(kv1)

# read from r2 x
incoming_kv = key_version.from_string(payload)
#print(kv2)
# is the clients pyaload more recent?
#print(incoming_kv.get_version('x'))

assert(incoming_kv.get_version('x') > kv2.get_version('x'))
ts1 = kv1.get_timestamp('x')
kv1.incr('x', current_milli_time())
ts2 = kv1.get_timestamp('x')

assert(kv1.get_version('x') > kv2.get_version('x'))
assert(kv1.get_version('x') == 2)

kv2.set('x', kv1.get_version('x'), current_milli_time(), False)
assert(kv2.get_version('x') == 2)
assert(kv1.get_version('x') == kv2.get_version('x'))
assert(kv2.get_tombstone('x') == False)

kv2.set('x', kv1.get_version('x'), current_milli_time(), True)
assert(kv2.get_tombstone('x') == True)