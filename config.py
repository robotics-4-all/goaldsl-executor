import os
from dotenv import load_dotenv

load_dotenv()

USE_REDIS = int(os.getenv('USE_REDIS', 1))
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_USERNAME = os.getenv('REDIS_USERNAME', '')
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', '')
REDIS_DB = int(os.getenv('REDIS_DB', 0))

# LOCAL_REDIS = bool(os.getenv('LOCAL_REDIS', 'True') in ("True", "true"))
BROKER_TYPE = str(os.getenv('BROKER_TYPE', 'REDIS'))
BROKER_HOST = str(os.getenv('BROKER_HOST', 'localhost'))
BROKER_PORT = int(os.getenv('BROKER_PORT', 6379))
BROKER_SSL = bool(os.getenv('BROKER_SSL', 'False') in ('True', 'true'))
BROKER_USERNAME = str(os.getenv('BROKER_USERNAME', ''))
BROKER_PASSWORD = str(os.getenv('BROKER_PASSWORD', ''))

UID: str = str(os.getenv('UID', 'TEST'))
EXECUTE_MODEL_RPC = str(os.getenv('EXECUTE_MODEL_RPC', 'goaldsl.{ID}.deploy_sync')).replace('{ID}', UID)
EXECUTE_MODEL_SUB = str(os.getenv('EXECUTE_MODEL_SUB', 'goaldsl.{ID}.deploy')).replace('{ID}', UID)
HEARTBEATS = bool(os.getenv('HEARTBEATS', 'False') in ("True", "true"))
DEBUG = bool(os.getenv('DEBUG', 'False') in ("True", "true"))
EXECUTION_TIMEOUT = float(os.getenv('EXECUTION_TIMEOUT', 3600))
WAIT_FOR_EXECUTION_TERMINATION = bool(os.getenv('WAIT_FOR_EXECUTION_TERMINATION', 'False') in ("True", "true"))
KILL_ALL_GOALS_SUB = str(os.getenv('KILL_ALL_GOALS_SUB', 'goaldsl.{ID}.killall')).replace('{ID}', UID)
KILL_ALL_GOALS_RPC = str(os.getenv('KILL_ALL_GOALS_RPC', 'goaldsl.{ID}.killall_sync')).replace('{ID}', UID)
ZERO_LOGS = int(os.getenv('GOALDSL_ZERO_LOGS', 0))
LOG_LEVEL = os.getenv("GOALDSL_LOG_LEVEL", "INFO")
