from flask import Flask
from flask import request
from flask import Response
from json import dumps, loads

import sys
import os
import requests
import random
import threading

from key_version import key_version
from view_version import view_version

# References:
#   https://stackoverflow.com/questions/5998245/get-current-time-in-milliseconds-in-python

import time
current_milli_time = lambda: int(round(time.time() * 1000))

# 1. Is there a stale value error message?
    #supposing there is for now until we know more
# 2. For a GET, is payload passed as a query parameter?
    #for now, seems like a reasonable way to get payload in reads.

main = Flask(__name__)
view_env = os.environ.get('VIEW')
ip_port_env = os.environ.get('IP_PORT')
numShards = int(os.environ.get('S'))
print("VIEW  "+str(view_env))
print("IP_PORT "+ str(ip_port_env))

shardDictionary = {}

debug_store = {}
for i in range(0, numShards):
    shardDictionary[i] = [];

views = view_version()
if view_env:
    i = 0
    for ip in sorted(view_env.split(",")):
        # val, key = ip.split(':')
        # view_dict[key] = val
        shardDictionary[i % numShards].append(ip)
        views.set(ip, True, current_milli_time())
        i += 1

# Global variables
store = {}


shard_id = 0
# this must also happen when a reshard happens and we
# learn about it

for shard,view_list in shardDictionary.items():
    for view in view_list:
        if view == str(ip_port_env):
            shard_id = shard



kv = key_version()

def shard_for_key(key):
  return hash(key)%numShards

def get_view_string():
    return (",".join("{}".format(ip) if exists else "" for ip, exists in sorted(view_dict.items())))

#gossip
def propogate():
    it = iter(list(views.get_key_list()))
    while(True):
        time.sleep(.2)
        try:
            ip = next(it)
        except StopIteration:
            it = iter(list(views.get_key_list()))
            ip = next(it)

        #print("IP::::::::::::::::::::::::::::::::::::::", ip, ip_port_env)
        if ip != ip_port_env and views.get_state(ip) is True:
            try:
                # add views list to this endpoint, adding any new incoming views
                requests.put('http://'+ip+'/internal-gossip',
                    data={'payload': str(kv),
                    'store' : dumps(store),
                    'views' : views.gossip_view(ip_port_env),
                    'shard_id' : shard_id},
                    timeout = (1.5,1.5))
            except requests.ConnectionError:
                pass
            # if int(port) > int(selfport):
            #     for key, value in store.items():
            #         requests.put('http://'+ip+':'+port+'/keyValue-store/'+key, data = {'val': value})

        # pick random other replica
        # send, using some internal endpoint, our entire state (store, and kv)


        # in that internal endpoint:
            # for every key in the incoming state
                # check whether it exists in our state or not
                # if so:
                    # if incoming is more than our version
                        # update our own value, version, and timestamp from incoming
                    # if incmoing is the same as our version
                        #compare incoming and own timestamp
                        # if ours is more:
                            # do nothing
                        # if incoming is more:
                            # update value, version, greater incoming timestamp
                    # if less
                        # do nothing
                # if not:
                    # add it, and the version, timestamp from incoming



            #propogating node additions
            #for key, value in view_dict.items():
                #    requests.put('http://'+ip+':'+port+'/view', data = {'ip_port': value+':'+key})

def update(key, value, version, timestamp, tombstone):
    store[key] = value
    kv.set(key, version, timestamp, tombstone)

gossips = []
@main.route("/recvd-gossip")
def gossip_data():
    return Response(dumps(gossips))


# Sources of reshard
# A node detects its the only node left for a particular shard. (not api)
# A node is deleted - for now, always, but :
    # Potentially don't need a reshard on deletions
        #if there are still >1 nodes left in that shard, potentially some clever ordering of nodes coming in in the future
        # to make up for the missing one
        # can allow us to avoid a reshard

# a node is added - for now, avoids some small racey cases with things that occur simultaneously ( not really tested )



sent_obj = {"msg" : "no obj"}

# Announces to every node to re hash all of its keys
# and recompute its shard dictionary so it knows which nodes
# are now in which shards.

# pre: 2 * num_shards <= num_nodes
# post: request sent to all other replicas indicating details of reshard
def reshard(new_shard_quant):
    global shardDictionary
    shardDictionary = {}
    i = 0
    numShards = new_shard_quant
    for j in range(numShards):
        shardDictionary[j] = []
    for ip in sorted(views.get_key_list()):
        if views.get_state(ip):
            shardDictionary[i%new_shard_quant].append(ip)
            i+=1

    for ip in views.get_key_list():
        try:
            requests.put("http://" + ip + "/reshard", data={"shards": new_shard_quant, "views": dumps(shardDictionary)})
        except (requests.ConnectionError, requests.exceptions.Timeout):
            pass

my_obj = {"msg" : "no obj"}
@main.route("/obj")
def get_obj():
    return Response(dumps(sent_obj))


old_store = None
new_store = None
@main.route("/store-change")
def get_stores():
    return Response(dumps({"old" : old_store, "new" : new_store}))

@main.route("/reshard", methods=['PUT'])
def reshardapi():
    global shardDictionary
    global numShards
    global shard_id
    global kv
    global store
    global shard_for_key
    obj = request.form
    my_obj = obj
    incoming_shard_dict = loads(obj["views"])
    shardDictionary = {}
    for key in incoming_shard_dict:
        shardDictionary[int(key)] = incoming_shard_dict[key]

    numShards = int(obj["shards"])
    for shard_i in shardDictionary:
        if ip_port_env in shardDictionary[shard_i]:
            shard_id = shard_i


    # the keys that must be forwarded on
    # mapping shard id to list of {key, value, version} groups
    keyForwardDict = {}
    for s_id in range(numShards):
        keyForwardDict[s_id] = []

    delete_set = set()

    for key in store.keys():
        s = shard_for_key(key)
        debug_store[str(key) + "data"] = str(shard_for_key(key)) + " " + str(shard_id)
        if s != shard_id:
            keyForwardDict[s].append({
                "key" : key,
                "value" : store[key],
                "version" : kv.get_all(key)
            })
            delete_set.add(key)

    for key in delete_set:
        del store[key]
        del kv.data[key]


    for shard in keyForwardDict:
        if keyForwardDict[shard] != []:
            for view in shardDictionary[shard]:
                try:
                    resp = requests.put('http://'+view + "/reshardput",
                            data=dumps(keyForwardDict[shard]), timeout=(1.5,1.5))
                    break
                except (requests.ConnectionError, requests.exceptions.Timeout):
                    pass

    return Response()

@main.route("/internal-gossip", methods=['PUT'])
def gossip():
    obj = request.form
    incoming_kv = key_version.from_string(obj['payload'])
    incoming_store = loads(obj['store'])
    incoming_views = view_version.from_string(obj['views'])
    incoming_shard_id = int(obj['shard_id'])
    print(incoming_shard_id)
    gossips.append(obj)

    # check whether the incoming shard id matches ours
    # if so, bring in their store, views, and shard data
    # if not, just bring in their views and shard data (dont worry about their keys)

    if incoming_shard_id == shard_id:
        for key in incoming_store:
            if shard_for_key(key) == shard_id:
                if key in store:
                    our_version = kv.get_version(key)
                    incoming_version = incoming_kv.get_version(key)
                    if our_version < incoming_version:
                        update(key, incoming_store[key], incoming_kv.get_version(key), incoming_kv.get_timestamp(key), incoming_kv.get_tombstone(key))
                    elif our_version == incoming_version:
                        our_timestamp = kv.get_timestamp(key)
                        incoming_timestamp = incoming_kv.get_timestamp(key)
                        if incoming_timestamp > our_timestamp:
                            update(key, incoming_store[key], incoming_kv.get_version(key), incoming_kv.get_timestamp(key), incoming_kv.get_tombstone(key))

                        # if equal, or our timestamp is max, do nothing

                    # otherwise, our version is more, so do nothing.

                else:
                    update(key, incoming_store[key], incoming_kv.get_version(key), incoming_kv.get_timestamp(key), incoming_kv.get_tombstone(key))

    for view in incoming_views.get_key_list():
        # assuming we are only ever out of date by maximum one view
        # since we delay client when they add a view, we will have already
        # propagated the single view by the time they add another.
        # This does theoretically have issues with multiple clients
        # simultaneously making add a view requests to different
        # replicas.
        if not view in views.get_key_list():
            shardDictionary[len(views) % numShards].append(view)
        if views.get_timestamp(view) < incoming_views.get_timestamp(view):
            views.set(view,
                incoming_views.get_state(view),
                incoming_views.get_timestamp(view))
    return Response()

def forward(subject, data, method, endpoint, key_shard):
    resp = None
    for view in shardDictionary[key_shard]:
        try:
            resp = method('http://'+view + endpoint + str(subject),
                    data=data, timeout=(1.5,1.5))
            break
        except (requests.ConnectionError, requests.exceptions.Timeout):
            pass
    if resp == None:
        # if we get here, our resharding has gone wrong.
        # Should trigger resharding logic rather than returning an error.

        return Response(dumps({"result": "Error",
            "msg": "All replicas responsible for the shard on which that key belongs are dead."}),
            status=200)
    return Response(dumps(resp.json()), status=resp.status_code)

@main.route("/reshard-put", methods=['PUT'])
def reshardput():
    obj = request.form
    for item in obj:
        key = item["key"]
        value = item["value"]
        version = item["version"]
        if shard_for_key(key) == shard_id:
            store[key] = value
            kv.set(key, version[0], version[1], version[2])
    return Response()

@main.route("/keyValue-store/<subject>", methods=['PUT', 'GET', 'DELETE'])
def keyvalue(subject):
    if len(subject) > 200:
        return Response(dumps({'msg' : 'Error',
                                  'error' : 'Key not valid'}),
                       status=400)

    if request.method == 'GET':
        obj = request.form
        #formatting incoming payload
        try:
            payload = obj['payload'].replace("\\", "").strip("\"")
        except:
            payload = obj['payload']
        print("str_payload "+str(payload))
        if payload == None:
            return Response(dumps({'error' : 'Payload is missing',
                                   'msg' : 'Error'}), status=400)
        # same as put - if we don't own this key, find somebody who does and
        # ask them about it.
        key_shard = shard_for_key(subject)

        if not key_shard == shard_id:
            return forward(subject, obj, requests.get, '/keyValue-store/', key_shard)

        incoming_kv = key_version.from_string(payload)

        if incoming_kv.get_version(subject) > kv.get_version(subject):
            return Response(dumps({'result' : 'Error',
                                   'msg' : 'Unable to serve request and maintain causal consistency',
                                   'payload' : str(kv)}), status=400)

        if kv.get_tombstone(subject):
            return Response(dumps({'result' : 'Error',
                                    'msg' : 'Key does not exist',
                                    'payload' : str(kv)}), status=404)

        try:

            for key in incoming_kv.data:
                if incoming_kv.get_version(key) < kv.get_version(key):
                    incoming_kv.set(key, kv.get_version(key), kv.get_timestamp(key), kv.get_tombstone(key))

            return Response(dumps({'result' : 'Success',
                                    'value' : store[subject],
                                    'owner' : str(shard_id),
                                    'payload' : str(incoming_kv)}), status=200)
        except KeyError:
            return Response(dumps({'result' : 'Success',
                                    'msg' : 'Key does not exist',
                                    'payload' : str(incoming_kv)}), status=404)
    # x = 1
    # 2 cases: x belongs on the shard this replica is responsible for
    # or it doesn't.

    # if it does, put it in our kv and store and respond.
    # if not, forward the request to all replicas responsible for the appropriate shard


    elif request.method == 'PUT':
        obj = request.form
        if obj == None:
            return Response(status=400)
        print("subject =", subject, "====", obj)
        if not 'val' in obj:
            return Response(dumps({'error' : 'Value is missing',
                                   'msg' : 'Error'}), status=400)
        if not 'payload' in obj:
            return Response(dumps({'error' : 'Payload is missing',
                                   'msg' : 'Error'}), status=400)

        # check if incoming key aka subject belongs in the shard
        # for which we are responsible.

        # if so, do the below

        # if not, forward request to node(s) with the shard the key belongs on
        key_shard = shard_for_key(subject)

        if not key_shard == shard_id:
            return forward(subject, obj, requests.put, '/keyValue-store/', key_shard)

        val = obj['val']
        try:
            payload_str = obj['payload'].replace("\\", "").strip("\"")
        except:
            payload_str = obj['payload']


        incoming_kv = key_version.from_string(payload_str)



        # Write from client, have their payload and our own kv.
        # Let us set our version to one more of whichever version between
        # the client's and our own is more recent.
        # In the common case that this is a totally new write, both our version
        # and the client's version are 0, and the new version is 1.
        new_version = max((incoming_kv.get_version(subject), kv.get_version(subject)))+1

        kv.set(subject, new_version, current_milli_time(), False)

        # Update any keys the client has that we have
        # newer versions of
        for key in incoming_kv.data:
            if incoming_kv.get_version(key) < kv.get_version(key):
                incoming_kv.set(key, kv.get_version(key), kv.get_timestamp(key), kv.get_tombstone(key))
        # Update the client on the key they wanted to write to.
        incoming_kv.set(subject, kv.get_version(subject),
                kv.get_timestamp(subject), kv.get_tombstone(subject))

        if len(val) > 1048576: # If the length of the value is too big
            return Response(dumps({'msg' : 'Error',
                                  'error' : 'Key not valid'}))
        if subject in store and not kv.get_tombstone(subject): # Replacing an existing key
            store[subject] = val
            return Response(dumps({'replaced' : True,
                                    'msg' : 'Updated successfully',
                                    'payload' : str(incoming_kv)}), status=200)
        else:   # New key being inserted
            store[subject] = val
            return Response(dumps({'replaced' : False,
                                   'msg' : 'Added successfully',
                                   'payload' : str(incoming_kv)}), status=201)
    elif request.method == 'DELETE':
        obj = request.form
        if obj == None:
            return Response(status=400)
        if not 'payload' in obj:
            return Response(dumps({'error' : 'Payload is missing',
                                   'msg' : 'Error'}), status=400)
        key_shard = shard_for_key(subject)

        if not key_shard == shard_id:
            return forward(subject, obj, requests.delete, '/keyValue-store/', key_shard)

        try:
            payload_str = obj['payload'].replace("\\", "").strip("\"")
        except:
            payload_str = obj['payload']

        incoming_kv = key_version.from_string(payload_str)
        new_version = max((incoming_kv.get_version(subject), kv.get_version(subject)))+1


        if not subject in store or kv.get_tombstone(subject):
            return Response(dumps({'result' : 'Error',
                                   'msg' : 'Key does not exist',
                                   'payload' : str(incoming_kv)}), status=404)
        else:
            kv.set(subject, new_version, current_milli_time(), True)
            # Update any keys the client has that we have
            # newer versions of
            for key in incoming_kv.data:
                if incoming_kv.get_version(key) < kv.get_version(key):
                    incoming_kv.set(key, kv.get_version(key), kv.get_timestamp(key), kv.get_tombstone(key))
            # Update the client on the key they wanted to write to.
            incoming_kv.set(subject, kv.get_version(subject),
                    kv.get_timestamp(subject), kv.get_tombstone(subject))
            return Response(dumps({'result' : 'Success',
                                    'msg' : 'Key deleted',
                                    'payload' : str(incoming_kv)}), status=200)
    else:
        return "Method not allowed"


# Searching
@main.route("/keyValue-store/search/<subject>", methods=['GET'])
def keyValue2(subject):
    if request.method == 'GET':
        obj = request.form


        if not 'payload' in obj:
            return Response(dumps({'error' : 'Payload is missing',
                                   'msg' : 'Error'}), status=400)

        key_shard = shard_for_key(subject)

        if not key_shard == shard_id:
            return forward(subject, obj, requests.get, '/keyValue-store/search/', key_shard)

        #print("SEARCH payload: "+str(payload))
        try:
            payload_str = obj['payload'].replace("\\", "").strip("\"")
        except:
            payload_str = obj['payload']
        incoming_kv = key_version.from_string(payload_str)

        if not subject in store or kv.get_tombstone(subject):
            return Response(dumps({'isExists': False,
                                    'result' : 'Success',
                                    'payload' : str(incoming_kv)}), status=200)

        if incoming_kv.get_version(subject) > kv.get_version(subject):
            return Response(dumps({'result' : 'Error',
                                   'msg' : 'Unable to serve request and maintain causal consistency',
                                   'payload' : str(kv)}), status=400)

        for key in incoming_kv.data:
            if incoming_kv.get_version(key) < kv.get_version(key): #includes the case where incoming kv doesn't have key at all, because a key that DNE returns version 0
                incoming_kv.set(key, kv.get_version(key), kv.get_timestamp(key), kv.get_tombstone(key))

        return Response(dumps({ 'isExists': True,
                                'result' : 'Success',
                                'owner' : str(shard_id),
                                'payload' : str(incoming_kv)}), status=200)

    else:
        return "Method not allowed"

@main.route("/view", methods=['PUT', 'GET', 'DELETE'])
def view():
    if request.method == 'GET':
        return Response(dumps({'view' : views.get_viewString()}), status=200)
    elif request.method == 'PUT':
        obj = request.form
        new_view = obj['ip_port']
        if new_view in views.get_key_list() and views.get_state(new_view):
            return Response(dumps({'result' : 'Error',
                                    'msg' : new_view+' is already in view'
                                    }), status=404)
        else:
            shardDictionary[len(views) % numShards].append(new_view)
            views.set(new_view, True, current_milli_time())


            reshard(numShards)
            time.sleep(0.8)
            return Response(dumps({'result' : 'Success',
                                    'msg' : 'Successfully added '+new_view+' to view'
                                    }), status=200)
    elif request.method == 'DELETE':
        obj = request.form
        del_view = obj['ip_port']
        if del_view in views.get_key_list():
            views.set(del_view, False, current_milli_time())
            # reshard, because the shard_id of every node potentially
            # changes when one is removed

            # For now, just reshard on every delete().
            # potentially in the future
            # check if we need to reshard:
                # reshard if only 1 node in a view
                # reshard if difference between number of nodes in a shard is >1

            # if we're resharding down to 1 replica in a shard, need to reduce #shards
            live_views = 0
            for key in views.get_key_list():
                if views.get_state(key):
                    live_views += 1

            if live_views > 1:
                if live_views < numShards * 2:
                    reshard(numShards-1)
                else:
                    reshard(numShards)
            else: # i'm the only one left!
                shardDictionary[0] = [ip_port_env]


            time.sleep(0.8)
            return Response(dumps({'result' : 'Success',
                                   'msg' : 'Successfully removed '+del_view+' from view'
                                  }), status=200)
        else:
            return Response(dumps({'result' : 'Error',
                                   'msg' : del_view+' is not in current view'
                                  }), status=404)
    else:
        return "Method not allowed"

@main.route('/everything')
def get_all_state():
    return Response(dumps({'debug_store' : debug_store, 'shard_id' : shard_id, 'state' : store, 'views' : str(views), 'kv' : str(kv), 'shards' : str(shardDictionary)}))


@main.route('/shard/my_id')
def get_shard_id():
    return Response(dumps({'id' : shard_id}))

def get_shard_ids():
    ids = []
    for shard in shardDictionary.keys():
        ids.append(str(shard))
    shard_ids = ",".join(ids)
    return shard_ids
@main.route('/shard/all_ids')
def get_all_shard_ids():
    return Response(dumps({'result' : 'Success', 'shard_ids' : get_shard_ids()}))

@main.route('/shard/members/<shard_id>')
def get_shards_with_id(shard_id):
    try:
        replicas = shardDictionary[int(shard_id)]
    except:
        return Response(dumps({"result" : "Error", "msg" : "No shard with id " + shard_id}), status=404)
    replica_string = ",".join(replicas)
    return Response(dumps({"result" : "Success", "members" : replica_string}))


# should deal with the required shard # logic before resharding


# two shards, first with 3 nodes and second with 2
# we kill the two nodes of the second shard.




@main.route('/shard/changeShardNumber', methods=['PUT'])
def change_shard_number():
    obj = request.form
    new_shard_quant = int(obj['num'])
    if new_shard_quant < 1:
        return Response(dumps({"result": "Error", "msg" : "Must have at least one shard"}), status=400)

    if new_shard_quant > len(views.get_key_list()):
        return Response(dumps({"result": "Error", "msg" : "Not enough nodes for " + str(new_shard_quant) + " shards"}), status=400)
    if len(views.get_key_list()) == 1:

        return Response(dumps({"result": "Success", "shard_ids" :"0"}), status=200)
    # need at least two nodes per shard
    if new_shard_quant * 2 > len(views.get_key_list()):
        return Response(dumps({"result" : "Error", "msg":
            "Not enough nodes. " + str(new_shard_quant) + " shards result in a nonfault tolerant shard"}), status=400)
    reshard(new_shard_quant)

    time.sleep(0.8)
    return Response(dumps({"result": "Success", "shard_ids" : get_shard_ids()}))

if __name__ == "__main__":
    #t1 = threading.Thread(target=main.run, args=('0.0.0.0', '8080'))
    t2 = threading.Thread(target=propogate)
    #t1.start()
    t2.start()
    #p1 = mp.Process(target=main.run, args=('0.0.0.0', '8080'))
    #p2 = mp.Process(target=propogate)
    #p1.start()
    #p2.start()
    main.run('0.0.0.0', '8080', debug=True)
