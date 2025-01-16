#!/usr/bin/env python

import sys
import time

from commlib.msg import PubSubMessage
from commlib.node import Node


class KillAllAsyncMsg(PubSubMessage):
    pass


if __name__ == "__main__":
    if len(sys.argv) < 2:
        broker = "redis"
    else:
        broker = str(sys.argv[1])
    if broker == "redis":
        from commlib.transports.redis import ConnectionParameters
    elif broker == "amqp":
        from commlib.transports.amqp import ConnectionParameters
    elif broker == "mqtt":
        from commlib.transports.mqtt import ConnectionParameters
    else:
        print("Not a valid broker-type was given!")
        sys.exit(1)
    conn_params = ConnectionParameters()

    node = Node(
        node_name="test_hello",
        connection_params=conn_params,
        heartbeats=False,
    )

    pub = node.create_publisher(
        msg_type=KillAllAsyncMsg, topic="goaldsl.651fc502286950d784cf8022.killall"
    )

    node.run(wait=True)

    # Create an instance of the request object
    msg = KillAllAsyncMsg()

    while True:
        time.sleep(1)
        pub.publish(msg)
