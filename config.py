import os
from dotenv import load_dotenv

load_dotenv()


def _env_bool(name: str, default: str = 'False') -> bool:
    """Parse a boolean flag from the environment.

    Accepts the usual truthy spellings so that e.g. `USE_REDIS=True` does not crash.
    """
    return str(os.getenv(name, default)).strip().lower() in ('1', 'true', 'yes', 'on')


# Redis Parameters (used for the local/executor node)
USE_REDIS = _env_bool('USE_REDIS', 'True')
REDIS_HOST = str(os.getenv('REDIS_HOST', 'localhost'))
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_USERNAME = str(os.getenv('REDIS_USERNAME', '')).strip()
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', '')
REDIS_DB = int(os.getenv('REDIS_DB', 0))
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
