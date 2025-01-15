import os
from dotenv import load_dotenv

load_dotenv()

BROKER_TYPE = str(os.getenv('BROKER_TYPE', 'REDIS'))
BROKER_HOST = str(os.getenv('BROKER_HOST', 'localhost'))
BROKER_PORT = int(os.getenv('BROKER_PORT', 6379))
BROKER_SSL = bool(os.getenv('BROKER_SSL', 'False') in ('True', 'true'))
BROKER_USERNAME = str(os.getenv('BROKER_USERNAME', ''))
BROKER_PASSWORD = str(os.getenv('BROKER_PASSWORD', ''))

UID: str = str(os.getenv('UID', 'TEST'))
EXECUTE_MODEL_RPC = str(os.getenv('EXECUTE_MODEL_RPC', 'goaldsl.{ID}.deploy_sync')).replace('{ID}', UID)
EXECUTE_MODEL_SUB = str(os.getenv('EXECUTE_MODEL_SUB', 'goaldsl.{ID}.deploy')).replace('{ID}', UID)
HEARTBEATS = bool(os.getenv('HEARTBEATS', False))
DEBUG = bool(os.getenv('DEBUG',False))
EXECUTION_TIMEOUT = float(os.getenv('EXECUTION_TIMEOUT', 3600))
WAIT_FOR_EXECUTION_TERMINATION = bool(os.getenv('WAIT_FOR_EXECUTION_TERMINATION', False))
