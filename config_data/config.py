from configparser import ConfigParser

config = ConfigParser()
config.read("config.ini")

TOKEN = config["settings"]["token"]
DIR_PATH = config["settings"]["dirpath"]
TIMEOUT = int(config["settings"]["timeout"])
