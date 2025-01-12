#! /usr/bin/env python3

import random
import string
import subprocess
import sys
import threading
import time
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


class CodeRunnerState:
    IDLE = 0
    RUNNING = 1
    TERMINATED = 2


class CodeRunner:
    def __init__(self, code: str, timeout: float = None):
        self._code = code
        self._state = CodeRunnerState.IDLE
        self._timeout = timeout
        self._uid = CodeRunner.generate_random_string()

    @staticmethod
    def generate_random_string(length: int = 16) -> str:
        """Generate a random string of fixed length."""
        letters = string.ascii_lowercase
        return ''.join(random.choice(letters) for _ in range(length))

    @property
    def state(self) -> CodeRunnerState:
        return self._state

    @property
    def elapsed_time(self) -> float:
        return round(time.time() - self._start_t, 2)

    def run(self, wait: bool = True):
        self._state = CodeRunnerState.RUNNING
        self._start_t = time.time()
        self._run_subprocess(wait)
        logging.info(f"Started CodeRunner <{self._uid}>")

    def stop(self):
        self._state = CodeRunnerState.TERMINATED
        self.force_exit()
        logging.info(f"Terminated CodeRunner <{self._uid}>")

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
        self._stdout_thread.start()
        self._stderr_thread.start()
        if wait:
            self._process.wait()
            self._stdout_thread.join()
            self._stderr_thread.join()

    def force_exit(self):
        self._process.terminate()
        self._stdout_thread.join(1)
        self._stderr_thread.join(1)
        self._process.wait(1)

    def report(self):
        if self._process.returncode != 0:
            logging.error(f"Subprocess failed with return code {self._process.returncode}")
        else:
            logging.info("Subprocess completed successfully!")


class GoalDSLExecutorNode(Node):
    def __init__(self, *args, **kwargs):
        super().__init__(node_name="goadsl-executor", *args, **kwargs)
        self._rate = Rate(100)  # 100 Hz
        self._runners = []
        self._execution_timeout = config.EXECUTION_TIMEOUT  # 2 seconds

    def start(self):
        logging.info("Starting GoadslExecutorNode...")
        self.report_conn_params()
        self._init_endpoints()
        self.run()
        while True:
            self.tick()
            self._rate.sleep()

    def tick(self):
        for runner in self._runners:
            timeout_cond = runner.elapsed_time >= self._execution_timeout \
                if self._execution_timeout is not None else False
            if runner and runner.state == CodeRunnerState.RUNNING and timeout_cond:
                runner.stop()

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
            logging.info("Running code-generator on input model")
            code = generate_str(model)
            logging.info("Running code-runner on generated code")
            code_runner = CodeRunner(code)
            code_runner.run(wait=config.WAIT_FOR_EXECUTION_TERMINATION)
            self._runners.append(code_runner)
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
