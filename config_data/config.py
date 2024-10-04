from configparser import ConfigParser

from logging_data.logger import logger

config = ConfigParser()
config.read("config.ini")
error_mesage = None

TOKEN = config["settings"]["token"]
DIR_PATH = config["settings"]["dirpath"]
timeout_conf = config["settings"]["timeout"]

if not TOKEN:
    error_mesage = "отсутствует token в config.ini"
elif not DIR_PATH:
    error_mesage = "отсутствует dirpath в config.ini"
elif not timeout_conf:
    error_mesage = "отсутствует timeout в config.ini"

try:
    TIMEOUT = int(timeout_conf)
except ValueError:
    error_mesage = "timeout в config.ini должен быть числом"

if error_mesage:
    logger.error(f"ошибка: {error_mesage}")
    exit()



