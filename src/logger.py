import logging
import sys
from pathlib import Path

# Создание директории для логов
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# Настройка форматирования
formatter = logging.Formatter(
    fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)
console_handler.setLevel(logging.INFO)

# File handler
file_handler = logging.FileHandler(log_dir / "battleship.log")
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.DEBUG)

# Error file handler
error_handler = logging.FileHandler(log_dir / "error.log")
error_handler.setFormatter(formatter)
error_handler.setLevel(logging.ERROR)

# Настройка основного логгера
logger = logging.getLogger("battleship")
logger.setLevel(logging.DEBUG)
logger.addHandler(console_handler)
logger.addHandler(file_handler)
logger.addHandler(error_handler)

# Отключение избыточных логов от сторонних библиотек
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
logging.getLogger("asyncio").setLevel(logging.WARNING)


__all__ = [
    'logger'
]
