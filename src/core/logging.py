"""Настройка централизованного логирования приложения через Loguru."""

import logging
import sys

from loguru import logger

from src.core.config import settings


class InterceptHandler(logging.Handler):
    """
    Перехват логов.

    Перехватывает стандартные логи logging (Uvicorn, FastAPI, SQLAlchemy)
    и направляет их в Loguru.
    """

    def emit(self, record: logging.LogRecord) -> None:
        """
        Перехватывает запись логирования из стандартного logging и отправляет её в Loguru.

        Args:
        record (logging.LogRecord): Объект записи журнала, созданный библиотекой
            logging, содержащий уровень, сообщение, исключение и метаданные события.

        """
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = logging.currentframe(), 2
        while frame.f_back and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def setup_logging() -> None:
    """Настраивает консольный и файловый вывод логов."""
    # Создаём директорию из настроек конфига, если её ещё нет
    settings.log.dir.mkdir(parents=True, exist_ok=True)

    logger.remove()

    # 1. Поток в stdout (Docker консоль)
    logger.add(
        sys.stdout,
        level=settings.log.level.upper(),
        format=settings.log.format,
        colorize=True,
    )

    # 2. Поток в файл
    logger.add(
        settings.log.dir / "app_{time:YYYY-MM-DD}.log",
        level=settings.log.level.upper(),
        format=settings.log.format,
        rotation=settings.log.rotation,
        retention=settings.log.retention,
        compression="zip",
        encoding="utf-8",
    )

    # 3. Перехват логов Uvicorn и стандартной библиотеки
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    for uvicorn_logger_name in ("uvicorn", "uvicorn.access", "uvicorn.error"):
        logging_logger = logging.getLogger(uvicorn_logger_name)
        logging_logger.handlers = [InterceptHandler()]
