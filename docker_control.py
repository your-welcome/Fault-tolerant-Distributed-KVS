# docker_control.py
# Docker Controls from Python
# Mostly called from hw3_test.py to start containers
# can be used from command line (largely for testing specific executions by hand)

# last update: 11/28/18 - Updated for HW4
# past updates: 
# 11/19/18 - cleaned up many of the getoutput commands to be strings
#          - added some functionality to interface with Blockade (don't worry about that stuff too much) 
# 11/17/18 - altered to use subnets, because Linux and Mac need them
#          - also will spin up multiple containers from comand line at once now 

import subprocess
import os
import sys
import time
import argparse

class docker_controller:
    sudo = []
    spinUpTime = 5
    verbose = False

    def __init__(self,mynet, needSudo=False):
        self.mynet = mynet
        if needSudo:
            self.sudo = ["sudo"]

    def dPrint(self, string, printIt, indentation=0):
        if printIt:
            print("%s%s"%("\t"*indentation, string))

    def buildDockerImage(self, tag):
        subprocess.run(self.sudo+["docker", "build", "-t", tag, "."])

    def spinUpDockerContainerNoWait(self, tag, hostIp, networkIP, port, view, numShards=1):
        #print("spinning docker container: %s:%s"%(hostIp, port))

        
        instance = {"testScriptAddress":hostIp+":"+port,
                    "networkIpPortAddress": networkIP+":8080"}

        command = self.sudo+["docker", "run", 
                        "-p", "%s:8080"%port, 
                        "--net=%s"%self.mynet,
                        "--ip=%s"%networkIP,
                        "-e", "VIEW=%s"%view, 
                        "-e", "IP_PORT=%s:8080"%networkIP, 
                        "-e", "S=%s"%numShards,
                        "-d", tag]

        # print(command)

        instance["containerID"] = subprocess.getoutput(" ".join(command))

        if " " in instance["containerID"]:
            print(instance["containerID"])

        self.dPrint(instance["containerID"], self.verbose, 1)

        return instance

    def spinUpDockerContainer(self, tag, hostIp, networkIP, port, view, numShards=1):
        instance = self.spinUpDockerContainerNoWait(tag, hostIp, networkIP, port, view, numShards)

        time.sleep(self.spinUpTime)

        #print("completed spinning docker container %s"%instance)

        return instance

    def spinUpManyContainers(self, tag, host_ip, network_ip_prefix, port_prefix, number, numShards=1):
        view = []
        for i in range(2, 2+number):
            view.append( "%s%s:%s0"%(network_ip_prefix, i, port_prefix) )

        viewString = ",".join(view)
        view = []
        for i in range(2, 2+number):
            view.append(self.spinUpDockerContainerNoWait(tag, host_ip, network_ip_prefix+str(i), port_prefix+str(i), viewString, numShards))

        time.sleep(self.spinUpTime)

        #print("completed spinning docker containers")

        return view

    def addToBlockade(self, instance):
        subprocess.run(self.sudo + ["blockade", "add", instance])

    def prepBlockade(self, instanceList):
        for instance in instanceList:
            self.addToBlockade(instance)

    def partitionContainer(self, partitionList):
        command = self.sudo + ["blockade", "partition" ] + partitionList

        subprocess.run(command)

    def healPartitions(self):
        command = self.sudo + ["blockade", "join"]
        subprocess.run(command)

    def blockadeStatus(self):
        command = self.sudo + ["blockade", "status"]
        subprocess.run(command)

    def tearDownBlockade(self):
        command = self.sudo + ["blockade", "destroy"]
        subprocess.run(command)

    def cleanUpDockerContainer(self, instance=None):
        if instance == None:
            #print("cleaning up all docker containers")

            command = " ".join(self.sudo+["docker", "ps", "-q"])

            instance = subprocess.getoutput(command)

            instance = instance.split("\n")

            for inst in instance:
                command = " ".join(self.sudo+["docker", "kill", inst])

                output = subprocess.getoutput(command)
                self.dPrint(output, self.verbose, 1)

        else:
            #print("cleaning up container %s"%instance)
            command = " ".join(self.sudo+["docker", "kill", instance])

            output = subprocess.getoutput(command)

            self.dPrint(output, self.verbose, 1)

        #print("done cleaning")

    def ps(self):
        subprocess.run(self.sudo+["docker", "ps"])



if __name__ == '__main__':
    #change these variables to change default values
    standardPortPrefix = "808"
    standardIP   = "localhost"
    standardNetworkIPPrefix = "192.168.0."
    standardBuildTag = "testing"
    standardNetworkName = "mynetwork"
    standardShardNumber = "2"

    parser = argparse.ArgumentParser(description='docker controller')
    parser.add_argument('-K', dest="is_kill_mode", action="store_true", 
        help="kill all docker containers that are running")

    parser.add_argument('-B', dest="is_build_mode", action="store_true", 
        help="build a docker image")

    parser.add_argument('-S', dest="is_start_mode", action="store_true", 
        help="start up a docker container")

    parser.add_argument('-t', dest="buildTag", default=standardBuildTag, 
        help="set the build tag. If unset, tag will be: %s"%standardBuildTag)

    parser.add_argument('-n', dest="number", default=4, 
        help="set number of containers to start. If unset, 4 will start")

    parser.add_argument('--port', dest="localPortPrefix", default=standardPortPrefix, 
        help="set the port to start your container on. Only used with -S. If unset will be: %s"%standardPortPrefix)

    parser.add_argument('--hostIp', dest="hostIp", default=standardIP, 
        help="set the ip of your host machine. This is the address you should send curl requests to."\
        +" Only used with -S. If unset will be: %s"%standardIP)

    parser.add_argument('--networkIP', dest="networkIpPrefix", default=standardNetworkIPPrefix, 
        help="set the ip prefix of your network (everything up to the last period). This is the begining of the address your "\
        + "containers will use to talk to each other. Only used with -S. If unset will be: %s"%standardNetworkIPPrefix)

    parser.add_argument('--net', dest="network", default=standardNetworkName, 
        help="the name of your network. Only used with -S. If unset will be: %s"%standardNetworkName)

    parser.add_argument('-shardNum', dest="shardNumber", default=standardShardNumber, 
        help="the number of shards to begin with. Only used with -S. If unset will be: %s"%standardShardNumber)

    parser.add_argument('-v', dest="verbose_mode", action="store_true", 
        help="print everything docker would print normally")


    args = parser.parse_args()

    kill = args.is_kill_mode
    build = args.is_build_mode
    start = args.is_start_mode

    verbose = args.verbose_mode

    dockerBuildTag = args.buildTag
    containerNumber = int(args.number)
    localPortPrefix = args.localPortPrefix
    hostIp = args.hostIp
    networkIpPrefix = args.networkIpPrefix
    networkName = args.network
    shardNumber = args.shardNumber


    dc = docker_controller(networkName)
    dc.verbose = verbose

    if kill:
        dc.cleanUpDockerContainer()
    if build:
        dc.buildDockerImage(dockerBuildTag)
    if start:
        dc.spinUpManyContainers(dockerBuildTag, hostIp, networkIpPrefix, localPortPrefix, containerNumber, shardNumber)

        dc.ps()
    