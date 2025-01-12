#! /usr/bin/env python3

import subprocess
import sys
import threading
from commlib.node import Node
from commlib.utils import Rate
from commlib.msg import RPCMessage
from goal_dsl.codegen import generate_str
import config as config
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")


def stream_logger(stream, log_func):
    for line in iter(stream.readline, ""):
        log_func(line.strip())


class ExecuteModelMsg(RPCMessage):
    class Request(RPCMessage.Request):
        model: str

    class Response(RPCMessage.Response):
        status: int = 1
        result: str = ""


class CodeRunner:
    def __init__(self, code: str):
        self._code = code

    def run(self, wait: bool = True):
        return self._run_subprocess(wait)

    def _run_subprocess(self, wait: bool = True):
        self._process = subprocess.Popen(
            ["python3", "-c", self._code],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        self._stdout_thread = threading.Thread(target=stream_logger,
                                               args=(self._process.stdout, logging.info))
        self._stderr_thread = threading.Thread(target=stream_logger,
                                               args=(self._process.stderr, logging.error))
        if wait:
            self._stdout_thread.start()
            self._stderr_thread.start()

            self._stdout_thread.join()
            self._stderr_thread.join()
            self._process.wait()

    def force_exit(self):
        self._process.terminate()
        self._stdout_thread.join()
        self._stderr_thread.join()
        self._process.wait()

    def report(self):
        if self._process.returncode != 0:
            logging.error(f"Subprocess failed with return code {self._process.returncode}")
        else:
            logging.info("Subprocess completed successfully!")


class GoalDSLExecutorNode(Node):
    def __init__(self, *args, **kwargs):
        super().__init__(node_name="goadsl-executor", *args, **kwargs)
        self._rate = Rate(100)  # 100 Hz

    def start(self):
        logging.info("Starting GoadslExecutorNode...")
        self.report_conn_params()
        self._init_endpoints()
        self.run()
        while True:
            self.tick()
            self._rate.sleep()

    def tick(self):
        pass

    def report_conn_params(self):
        logging.info("Connection parameters:")
        logging.info(f" > Broker type: {config.BROKER_TYPE}")
        logging.info(f" > Broker host: {config.BROKER_HOST}")
        logging.info(f" > Broker port: {config.BROKER_PORT}")
        logging.info(f" > Broker SSL: {config.BROKER_SSL}")
        logging.info(f" > Broker username: {config.BROKER_USERNAME}")
        logging.info(f" > Broker password: {config.BROKER_PASSWORD}")
        logging.info(f" > Execute model RPC: {config.EXECUTE_MODEL_RPC}")
        logging.info(f" > Heartbeats: {config.HEARTBEATS}")
        logging.info(f" > Debug: {config.DEBUG}")

    def _init_endpoints(self):
        execute_model_endpoint = self.create_rpc(
            msg_type=ExecuteModelMsg,
            rpc_name=config.EXECUTE_MODEL_RPC,
            on_request=self.on_request_model_execution
        )
        logging.info(f"Registered RPC endpoint: {config.EXECUTE_MODEL_RPC}")
        self._execute_model_endpoint = execute_model_endpoint

    def on_request_model_execution(self, msg: ExecuteModelMsg.Request) -> ExecuteModelMsg.Response:
        try:
            model = msg.model
            logging.error(f"Running code-generator on input model: {model}")
            code = generate_str(model)
            logging.error(f"Executing code with CodeRunner: {code}")
            code_runner = CodeRunner(code)
            code_runner.run(wait=False)
            return ExecuteModelMsg.Response(status=1, result="Model executed successfully!")
        except Exception as e:
            logging.error(f"Error executing model: {e}", exc_info=False)
            return ExecuteModelMsg.Response(status=0, result=f"Error executing model: {str(e)}")


if __name__ == "__main__":
    broker = config.BROKER_TYPE
    if broker == "REDIS":
        from commlib.transports.redis import ConnectionParameters
    elif broker == "AMQP":
        from commlib.transports.amqp import ConnectionParameters
    elif broker == "MQTT":
        from commlib.transports.mqtt import ConnectionParameters
    else:
        print("Not a valid broker-type was given!")
        sys.exit(1)
    conn_params = ConnectionParameters(
        host=config.BROKER_HOST, port=config.BROKER_PORT,
        username=config.BROKER_USERNAME, password=config.BROKER_PASSWORD,
        ssl=config.BROKER_SSL
    )
    executor = GoalDSLExecutorNode(
        connection_params=conn_params,
        debug=config.DEBUG,
        heartbeats=config.HEARTBEATS
    )
    executor.start()
