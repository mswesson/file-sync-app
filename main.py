import asyncio

from config_data.config import DIR_PATH
from core.functions import (
    checking_remove_files,
    get_edit_files_paths,
    search_files_to_dir,
    sync_delete_file,
    sync_file,
)
from database.database import engine
from database.models import Base


async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    all_files = await search_files_to_dir(DIR_PATH)
    edit_files = await get_edit_files_paths(all_files)
    all_file_only_paths = [path_and_datetime[0] for path_and_datetime in all_files]
    deleted_files = await checking_remove_files(paths=all_file_only_paths)

    print("Все файлы: ", all_file_only_paths)
    print()
    print("Измененные файлы: ", edit_files)
    print()
    print("Удаленные файлы: ", deleted_files)

    for path in edit_files:
        await sync_file(path)

    for path in deleted_files:
        await sync_delete_file(path)


if __name__ == "__main__":
    asyncio.run(main())
