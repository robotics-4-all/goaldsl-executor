#!/usr/bin/env python

import sys
import time

from commlib.msg import RPCMessage
from commlib.node import Node


class ExecuteModelMsg(RPCMessage):
    class Request(RPCMessage.Request):
        model: str

    class Response(RPCMessage.Response):
        status: int = 1
        result: str = ""


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

    model_file = "scenario.goal"

    with open(model_file, "r") as f:
        model = f.read()
    print(model)

    conn_params = ConnectionParameters()

    node = Node(
        node_name="test_hello",
        connection_params=conn_params,
        heartbeats=False,
        # heartbeat_uri='nodes.add_two_ints.heartbeat',
        debug=True,
    )
    rpc = node.create_rpc_client(
        msg_type=ExecuteModelMsg, rpc_name="goadsl.executor.execute_model"
    )
    node.run()

    msg = ExecuteModelMsg.Request(model=model)
    resp = rpc.call(msg)
    print(resp)
