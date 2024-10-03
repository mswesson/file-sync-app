import asyncio
import os
from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy import select

from core.http_functions import delete_file_in_cloud, save_file_to_cloud
from database.database import async_session
from database.models import File


async def search_file_in_db_by_path(path: str) -> Optional[File]:
    """Ищет файл в ДБ по пути"""
    async with async_session() as db:
        file_elem_db = await db.execute(select(File).where(File.path == path))
        file_elem_db = file_elem_db.scalar()
        return file_elem_db


async def add_or_edit_file_in_db(
    edit_data: datetime, path: str = None, file: File = None
) -> None:
    """
    Добавляет или изменяет файл в ДБ

    Aтрибуты:
        edit_data (datetime): обязательный атрибут, корректное время изменения файла
        path (str): необязательный параметр, путь к файлу. Если передан данный параметр
            будет создан новый объект в БД
        file (File): необязательный параметр, файл из БД. Если был передан, то в БД
            будет изменен параметр времени изменения
    """
    async with async_session() as db:
        if path and file:
            raise AttributeError("path or file expected")
        elif path:
            file = File(path=path, edit_data=edit_data)
        elif file:
            file.edit_data = edit_data

        db.add(file)
        await db.commit()


async def checking_remove_files(paths: List[str]) -> List[Optional[str]]:
    """Выводит список путей к файлам, которых нет в переданном списке но есть в БД"""
    async with async_session() as db:
        response = await db.execute(select(File.path).where(~File.path.in_(paths)))
        response = response.scalars().all()
        return response


async def search_files_to_dir(path: str) -> Tuple[List[Optional[str]]]:
    """
    Выводит два списка. Один список отражает все пути к файлам, которые были найдены
    в дирректории. Второй список отражает только добавленные или измененные файлы.

    Атрибуты:
        path (str): путь к директории в которой будет происходить поиск

    Вывод:
        List[Optional[str]]: все пути к найденным файлам
        List[Optional[str]]: добавленные или измененные файлы

    """
    files_list = []
    files_by_dir = await asyncio.to_thread(os.listdir, path)

    for file_name in files_by_dir:
        file_path = os.path.join(path, file_name)
        if await asyncio.to_thread(os.path.isfile, file_path):  # проверка на файл
            # добавляю путь файла в список найденных файлов

            # получаю время изменения файла
            cur_edit_data_stamp = await asyncio.to_thread(os.path.getmtime, file_path)
            cur_edit_data = datetime.fromtimestamp(cur_edit_data_stamp)

            files_list.append((file_path, cur_edit_data))

        elif await asyncio.to_thread(
            os.path.isdir, file_path
        ):  # проверка на директорию
            result_wraper = await search_files_to_dir(file_path)
            files_list.extend(result_wraper)

    return files_list


async def get_edit_files_paths(pathes_and_datetime: List[tuple]) -> List[Optional[str]]:
    """Возвращает список путей к измененным файлам"""
    edit_files = []

    async with async_session() as db:
        all_files_in_db = await db.execute(select(File.path, File.edit_data))
        all_files_in_db = all_files_in_db.all()

    for cur_path_and_datetime in pathes_and_datetime:
        if not cur_path_and_datetime in all_files_in_db:
            edit_files.append(cur_path_and_datetime[0])

    return edit_files


async def sync_file(file_path: str):
    """Синхронизирует файл с облаком и БД"""
    status_save_to_cloud = await save_file_to_cloud(file_path=file_path)
    if not status_save_to_cloud:
        raise AttributeError(f"файл {file_path} не синхронизирован")

    file = await search_file_in_db_by_path(file_path)
    cur_edit_data_stamp = await asyncio.to_thread(os.path.getmtime, file_path)
    cur_edit_data = datetime.fromtimestamp(cur_edit_data_stamp)

    if not file:
        file = File(path=file_path, edit_data=cur_edit_data)
        print(f"Добавляю новый файл в облако {file_path.split("/")[-1]}")
    else:
        file.edit_data = cur_edit_data
        print(f"Обновляю файл в облаке {file_path.split("/")[-1]}")
    async with async_session() as db:
        db.add(file)
        await db.commit()


async def delete_file_in_db(file_path: str):
    """Удаляет файл из БД по пути"""
    file = await search_file_in_db_by_path(file_path)
    async with async_session() as db:
        await db.delete(file)
        await db.commit()
    return True


async def sync_delete_file(file_path: str):
    """Удаляет файл из облака и из БД"""
    delete_bd = await delete_file_in_db(file_path)
    delete_cloud = await delete_file_in_cloud(file_path)

    if not delete_bd or not delete_cloud:
        print("ошибка синхронизации удаления файла")
