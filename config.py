import os
from dotenv import load_dotenv

load_dotenv()


BROKER_HOST = str(os.getenv('BROKER_HOST', 'localhost'))
BROKER_PORT = int(os.getenv('BROKER_PORT', 1883))
BROKER_USERNAME = str(os.getenv('BROKER_USERNAME', ''))
BROKER_PASSWORD = str(os.getenv('BROKER_PASSWORD', ''))
