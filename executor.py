#! /usr/bin/env python3

import sys
from commlib.node import Node
from commlib.utils import Rate
from commlib.msg import RPCMessage
from goal_dsl.codegen import generate
import config as config



class ExecuteModelMsg(RPCMessage):
    class Request(RPCMessage.Request):
        model: str

    class Response(RPCMessage.Response):
        status: int = 1
        result: str = ""


class GoalDSLExecutorNode(Node):
    def __init__(self, *args, **kwargs):
        super().__init__(node_name="goadsl-executor", *args, **kwargs)
        self._rate = Rate(100)  # 100 Hz

    def start(self):
        self.run()
        while True:
            self.tick()
            self._rate.sleep()

    def tick(self):
        pass

    def _init_endpoints(self):
        execute_model_endpoint = self.create_rpc(
            msg_type=ExecuteModelMsg,
            rpc_name="goadsl.executor.execute_model",
            on_request=self.on_request_model_execution,
        )
        self._execute_model_endpoint = execute_model_endpoint

    def on_request_model_execution(self, msg: ExecuteModelMsg.Request) -> ExecuteModelMsg.Response:
        print(msg)


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
    executor = GoalDSLExecutorNode(connection_params=conn_params,
                               debug=True,)
    executor.start()
