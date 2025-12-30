# **LAB-2-Logical-Clocks-and-Replication-Consistency**

This repository contains an implementation of a replicated key–value store using
Lamport logical clocks and eventual consistency.
The system is deployed on three AWS EC2 instances (A, B, C) and demonstrates
causal ordering, last-writer-wins (LWW) conflict resolution, and convergence under
delays, concurrent writes, and temporary node failures.

# **Environment and infrastructure**

Three AWS EC2 instances were used.

Instance 1:
Name: node-A  
AMI: Ubuntu Server 22.04 LTS  
Instance type: t2.micro  
Public IPv4 address: enabled  

Instance 2:
Name: node-B  
AMI: Ubuntu Server 22.04 LTS  
Instance type: t2.micro  
Public IPv4 address: enabled  

Instance 3:
Name: node-C  
AMI: Ubuntu Server 22.04 LTS  
Instance type: t2.micro  
Public IPv4 address: enabled  

All instances were placed in the same VPC to allow internal communication using
private IP addresses.

# **Security group configuration**

A single security group was created and attached to all three instances with the
following inbound rules:

- SSH, TCP port 22, source: your IP
- Custom TCP, port 8000, source: security group
- Custom TCP, port 8001, source: security group
- Custom TCP, port 8002, source: security group

Ports 8000–8002 are used for HTTP-based communication between distributed nodes.

# **Prerequisites on all instances**

The following packages must be installed on each EC2 instance:

sudo apt update  
sudo apt install python3 -y  

Python version used:
python3 (system default on Ubuntu 22.04)

# **Files**

1) node.py  
Implements a distributed node participating in a replicated key–value store.
Each node:
- Maintains a Lamport logical clock
- Stores key–value pairs with timestamps and origin node
- Replicates updates to peer nodes using HTTP and JSON
- Resolves conflicts using Last-Writer-Wins (LWW)

Supported endpoints:
- POST /put
- POST /replicate
- GET /get?key=...
- GET /status

2) client.py  
Implements a simple HTTP client used to interact with nodes.
The client is used to:
- Issue PUT operations
- Read values using GET
- Inspect node state using STATUS

# **How to run**

1. Start the nodes (use private IPs)

Node A:
python3 node.py --id A --port 8000 \
--peers http://<IP-B>:8001,http://<IP-C>:8002

Node B:
python3 node.py --id B --port 8001 \
--peers http://<IP-A>:8000,http://<IP-C>:8002

Node C:
python3 node.py --id C --port 8002 \
--peers http://<IP-A>:8000,http://<IP-B>:8001

2. Run client operations

PUT operation:
python3 client.py --node http://<IP-A>:8000 put x 1

GET operation:
python3 client.py --node http://<IP-B>:8001 get x

STATUS check:
python3 client.py --node http://<IP-C>:8002 status

# **Demonstrated scenarios**

Scenario A — Message delay and reordering  
An artificial delay is introduced for replication messages from node A to node C.
Node B receives updates immediately, while node C applies them later.
Despite reordering, all nodes eventually converge to the same state.

Scenario B — Concurrent writes  
Simultaneous PUT operations on the same key are issued from different nodes.
Lamport timestamps determine the winning update using LWW semantics.

Scenario C — Temporary node outage  
Node C is stopped while updates occur on nodes A and B.
After restarting node C, missed updates are replicated and the system converges.

# **Expected behavior**

- Lamport clocks correctly advance on local events and message receipt
- Replicated updates propagate to all peers
- Conflicting writes resolve deterministically
- All nodes eventually converge to the same key–value state

This lab demonstrates causal ordering, eventual consistency, and fault tolerance
in a distributed system.
