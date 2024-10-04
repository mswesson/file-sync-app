import asyncio
from time import sleep

from config_data.config import DIR_PATH, TIMEOUT
from core.functions import (
    checking_remove_files,
    get_edit_files_paths,
    search_files_to_dir,
    sync_delete_file,
    sync_file,
)
from database.database import engine
from database.models import Base
from logging_data.logger import logger


async def start_app():
    """Создает БД и таблицы в ней, если не существует"""
    logger.info("запуск приложения")
    logger.debug("попытка создать БД, если её не существует")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info(f"синхронизируемая дирректория {DIR_PATH}")


async def main():
    all_files = await search_files_to_dir(DIR_PATH)
    edit_files = await get_edit_files_paths(all_files)
    all_file_only_paths = [path_and_datetime[0] for path_and_datetime in all_files]
    deleted_files = await checking_remove_files(paths=all_file_only_paths)

    for path in edit_files:
        await sync_file(path)

    for path in deleted_files:
        await sync_delete_file(path)


if __name__ == "__main__":
    try:
        asyncio.run(start_app())
        while True:
            asyncio.run(main())
            sleep(TIMEOUT)
    except KeyboardInterrupt:
        logger.info("остановка приложения")
        exit()
    except Exception as ex:
        logger.warning(ex)
