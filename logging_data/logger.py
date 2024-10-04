import logging
import logging.handlers

logger = logging.getLogger("my_logger")
logger.setLevel(logging.DEBUG)  # Устанавливаем уровень логирования

file_handler = logging.handlers.RotatingFileHandler(
    filename="logging_data/log.log",
    maxBytes=5000,
    backupCount=3,
)
file_handler.setLevel(logging.INFO)  # Уровень логирования для файла
file_format = logging.Formatter(
    "%(asctime)s [%(module)s.%(funcName)s] %(levelname)s - %(message)s"
)
file_handler.setFormatter(file_format)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)  # Уровень логирования для консоли
console_format = logging.Formatter(
    "[%(module)s.%(funcName)s] %(levelname)s - %(message)s"
)
console_handler.setFormatter(console_format)

logger.addHandler(file_handler)
logger.addHandler(console_handler)
