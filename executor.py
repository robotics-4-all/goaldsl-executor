#! /usr/bin/env python3

import os
import random
import string
import subprocess
import sys
import threading
import time
from commlib.node import Node
from commlib.utils import Rate
from commlib.msg import RPCMessage, PubSubMessage
from goal_dsl.generator import m2t_python_str
import config as config
import logging


# Set up logging
logging.basicConfig(format="%(asctime)s - %(message)s")
if config.ZERO_LOGS: logging.disable()
else: logging.getLogger().setLevel(config.LOG_LEVEL)
# -------------------------------------------------------------

def stream_logger(stream, log_func):
    for line in iter(stream.readline, ""):
        log_func(line.strip())


class ExecuteModelMsg(RPCMessage):
    class Request(RPCMessage.Request):
        model: str

    class Response(RPCMessage.Response):
        status: int = 1
        result: str = ""


class ExecuteModelAsyncMsg(PubSubMessage):
    model: str


class KillAllAsyncMsg(PubSubMessage):
    pass


class KillAllRPCMsg(RPCMessage):
    class Request(RPCMessage.Request):
        pass
    class Response(RPCMessage.Response):
        status: int = 1
        error: str = ""


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
        logging.warning(f'Stopping CodeRunner {self._uid}...')
        self.force_exit()

    def _run_subprocess(self, wait: bool = True):
        logging.info(f"Running Subprocess {self._uid} with flag wait={wait}...")
        self._process = subprocess.Popen(
            ["python3", "-c", self._code],
            env={**os.environ.copy(), "U_ID": self._uid},
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            # shell=True,
            text=True,
            bufsize=1
        )
        logging.info("Process started successfully")
        self._stdout_thread = threading.Thread(target=stream_logger,
                                               args=(self._process.stdout, logging.info))
        self._stderr_thread = threading.Thread(target=stream_logger,
                                               args=(self._process.stderr, logging.error))
        self._stdout_thread.start()
        self._stderr_thread.start()
        logging.info("Started logging threads")
        if wait:
            logging.warning(f"Waiting for Coderunner <UID:{self._uid}> to terminate")
            self._process.wait()
            self._stdout_thread.join()
            self._stderr_thread.join()
            self._state = CodeRunnerState.TERMINATED
            logging.warning(f"CodeRunner <UID:{self._uid}> terminated")

    def force_exit(self):
        self._process.kill()
        self._stdout_thread.join(1)
        self._stderr_thread.join(1)
        self._process.wait(1)
        self._state = CodeRunnerState.TERMINATED
        logging.warning(f"CodeRunner <PID:{self._process.pid}> forcefully terminated")

    def report(self):
        if self._process.returncode != 0:
            logging.error(f"Subprocess failed with return code {self._process.returncode}")
        else:
            logging.info("Subprocess completed successfully!")


class GoalDSLExecutorNode(Node):
    def __init__(self, local_redis: bool = False, *args, **kwargs):
        super().__init__(node_name="goadsl-executor", *args, **kwargs)
        self._rate = Rate(100)  # 100 Hz
        self._local_redis = local_redis
        self._runners = []
        self._execution_timeout = config.EXECUTION_TIMEOUT  # 2 seconds
        self._thread = None
        self._tstop_event = threading.Event()

    def start(self):
        logging.info("Starting GoadslExecutorNode...")
        self.report_conn_params()
        self._init_endpoints()
        self.run()
        threading.Thread(target=self._run_tick_loop, daemon=True).start()

    def _run_tick_loop(self):
        while not self._tstop_event.is_set():
            self.tick()
            self._rate.sleep()

    def stop(self):
        logging.info("Stopping GoadslExecutorNode...")
        self._tstop_event.set()
        self._thread.join(1)

    def tick(self):
        for runner in self._runners:
            timeout_cond = runner.elapsed_time >= self._execution_timeout \
                if self._execution_timeout is not None else False
            if runner and runner.state == CodeRunnerState.RUNNING and timeout_cond:
                runner.stop()
        for runner in self._runners:
            if runner.state == CodeRunnerState.TERMINATED:
                self._runners.remove(runner)

    def report_conn_params(self):
        logging.info("Connection parameters:")
        logging.info(self._conn_params)

    def _init_endpoints(self):
        execute_model_rpc = self.create_rpc(
            msg_type=ExecuteModelMsg,
            rpc_name=config.EXECUTE_MODEL_RPC,
            on_request=self.on_request_model_execution
        )
        logging.info(f"Registered RPC endpoint: {config.EXECUTE_MODEL_RPC}")
        killall_goals_rpc = self.create_rpc(
            msg_type=KillAllRPCMsg,
            rpc_name=config.KILL_ALL_GOALS_RPC,
            on_request=self.on_request_killall
        )
        logging.info(f"Registered RPC endpoint: {config.KILL_ALL_GOALS_RPC}")
        execute_model_async_endpoint = self.create_subscriber(
            topic=config.EXECUTE_MODEL_SUB,
            on_message=self.on_message_execute_model,
            msg_type=ExecuteModelAsyncMsg
        )
        logging.info(f"Registered Subscriber endpoint: {config.EXECUTE_MODEL_SUB}")
        kill_all_goals_sub = self.create_subscriber(
            topic=config.KILL_ALL_GOALS_SUB,
            on_message=self.on_message_killall,
            msg_type=KillAllAsyncMsg
        )
        logging.info(f"Registered Subscriber endpoint: {config.KILL_ALL_GOALS_SUB}")
        self._execute_model_endpoint = execute_model_rpc
        self._execute_model_async_endpoint = execute_model_async_endpoint
        self._kill_all_goals_sub = kill_all_goals_sub
        self._kill_all_goals_rpc = killall_goals_rpc

    def on_request_model_execution(self, msg: ExecuteModelMsg.Request) -> ExecuteModelMsg.Response:
        logging.info("Received model execution request")
        try:
            self._deploy_model(msg.model)
            return ExecuteModelMsg.Response(status=1, result="Model executed successfully!")
        except Exception as e:
            logging.error(f"Error executing model: {e}", exc_info=False)
            return ExecuteModelMsg.Response(status=0, result=f"Error executing model: {str(e)}")

    def on_request_killall(self, msg: KillAllRPCMsg.Request) -> KillAllRPCMsg.Response:
        logging.info("Received KillAll request")
        try:
            self._killall_goals()
            return KillAllRPCMsg.Response(result="KillAll GoalDSL CodeRunners was successfully!")
        except Exception as e:
            logging.error(f"Error killing GoalDSL CodeRunners: {e}", exc_info=False)
            return KillAllRPCMsg.Response(status=0, result=f"Error killing GoalDSL CodeRunners: {str(e)}")

    def on_message_execute_model(self, msg: ExecuteModelAsyncMsg):
        logging.info("Received model execution request")
        try:
            self._deploy_model(msg.model)
        except Exception as e:
            logging.error(f"Error deploying model: {e}", exc_info=False)

    def on_message_killall(self, msg: KillAllAsyncMsg):
        logging.warning("Received KillAll request!!!")
        try:
            self._killall_goals()
        except Exception as e:
            logging.error(f"Error while terminating goal executions in coderunner: {e}",
                          exc_info=False)

    def _killall_goals(self):
        for runner in self._runners:
            runner.force_exit()

    def _deploy_model(self, model_str: str):
        logging.info("Running code-generator on input model")
        scenario_code: dict = m2t_python_str(model_str)
        logging.info("Running code-runner on generated code")
        for name, code in scenario_code.items():
            code_runner = CodeRunner(code)
            code_runner.run(wait=config.WAIT_FOR_EXECUTION_TERMINATION)
            self._runners.append(code_runner)


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
    if config.LOCAL_REDIS:
        from commlib.transports.redis import ConnectionParameters as RedisConnParams
        local_executor = GoalDSLExecutorNode(
            connection_params=RedisConnParams(),
            debug=config.DEBUG,
            heartbeats=config.HEARTBEATS
        )
        local_executor.start()
    while True:
        time.sleep(0.01)
