# Scalable Fault-tolerant-Distributed-KVS

#### This was a project for a course on distributed systems and was built in four parts:

## Part 1:
Create a REST API that can differentiate between GET and POST requests


## Part 2:  
Build a RESTful single-site key-value store and a network of proxies and instances that are capable of forwarding requests across proxies to the key-value store.


## Part 3:  
Building upon the key-value store in part two, add available fault-tolerance by adding causal and eventual consistency through replication.



## Part 4:
Taking the fault-tolerant key-value store made in part three and making it scalable by implementing the sharding of data across multiple nodes.  The system will determine the location of data based on the number of nodes in the system and the shard size.

Any changes made to shard size or number of nodes will cause the system to automatically respond by redistributing data to maintain a uniform distribution.

