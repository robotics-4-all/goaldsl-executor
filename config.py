import os
from dotenv import load_dotenv

load_dotenv()

BROKER_TYPE = str(os.getenv('BROKER_TYPE', 'REDIS'))
BROKER_HOST = str(os.getenv('BROKER_HOST', 'localhost'))
BROKER_PORT = int(os.getenv('BROKER_PORT', 6379))
BROKER_SSL = bool(os.getenv('BROKER_SSL', False))
BROKER_USERNAME = str(os.getenv('BROKER_USERNAME', ''))
BROKER_PASSWORD = str(os.getenv('BROKER_PASSWORD', ''))

EXECUTE_MODEL_RPC = str(os.getenv('EXECUTE_MODEL_RPC', 'goadsl.executor.execute_model'))
HEARTBEATS = bool(os.getenv('HEARTBEATS', False))
DEBUG = bool(os.getenv('DEBUG',False))
EXECUTION_TIMEOUT = float(os.getenv('EXECUTION_TIMEOUT', 3600))
