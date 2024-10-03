import os

from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")
DIR_PATH = os.getenv("DIR_PATH")
CHEKING_FILES_PERIOD = None
