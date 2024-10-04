import asyncio
import os
from datetime import datetime
from typing import List, Optional

from sqlalchemy import select

from core.http_functions import delete_file_in_cloud, save_file_to_cloud
from database.database import async_session
from database.models import File
from logging_data.logger import logger


async def search_file_in_db_by_path(path: str) -> Optional[File]:
    """Ищет файл в ДБ по пути"""
    async with async_session() as db:
        file_elem_db = await db.execute(select(File).where(File.path == path))
        file_elem_db = file_elem_db.scalar()
    return file_elem_db


async def checking_remove_files(paths: List[str]) -> List[Optional[str]]:
    """
    Определяет какие файлы есть в БД но нету локально,
    то есть определяет какие файлы необходимо удалить в облаке и БД
    """
    async with async_session() as db:
        response = await db.execute(select(File.path).where(~File.path.in_(paths)))
        response = response.scalars().all()

    logger.debug(
        "найдены удаленные файлы" if response else "не найдено удаленных файлов"
    )

    return response


async def search_files_to_dir(path: str) -> List[Optional[tuple]]:
    """
    Выводит список с кортежами, которые содержат в себе путь локального файла и его дату изменения

    Атрибуты:
        path (str): путь к директории в которой будет происходить поиск

    Вывод:
        List[Optional[tuple]]: пути локальных файлов и их дату изменения
    """
    files_list = []
    files_by_dir = await asyncio.to_thread(os.listdir, path)
    logger.debug(f"сканирую локальную папку {path}")

    for file_name in files_by_dir:
        file_path = os.path.join(path, file_name)
        if await asyncio.to_thread(os.path.isfile, file_path):  # проверка на файл
            # получаю время изменения файла
            cur_edit_data_stamp = await asyncio.to_thread(os.path.getmtime, file_path)
            cur_edit_data = datetime.fromtimestamp(cur_edit_data_stamp)
            # добавляю путь файла и время изменения в список files_list
            files_list.append((file_path, cur_edit_data))

        elif await asyncio.to_thread(
            os.path.isdir, file_path
        ):  # проверка на директорию
            result_wraper = await search_files_to_dir(file_path)
            files_list.extend(result_wraper)

    return files_list


async def get_edit_files_paths(pathes_and_datetime: List[tuple]) -> List[Optional[str]]:
    """
    Возвращает список путей к измененным файлам

    Атрибуты:
        pathes_and_datetime (list): должен содержать данные формата [(path (str), edit_date (datetime))]

    Вывод:
        list: список путей, файлов которые были измененеы
    """
    edit_files = []

    # загружаю информацию о файлах из БД
    async with async_session() as db:
        all_files_in_db = await db.execute(select(File.path, File.edit_data))
        all_files_in_db = all_files_in_db.all()

    # попеременно сравниваю локальные файлы с множеством файлов из БД
    # если совпадений не найдено, то файл является измененным
    for cur_path_and_datetime in pathes_and_datetime:
        if not cur_path_and_datetime in all_files_in_db:
            # добавляю в список путь измененного файла
            edit_files.append(cur_path_and_datetime[0])

    logger.debug(
        "найдены измененные файлы" if edit_files else "не найдено измененных файлов"
    )

    return edit_files


async def sync_file(file_path: str):
    """Загружает измененный файл в облако и БД"""
    file_name = file_path.split("/")[-1]
    # загружаем файл в облако
    status_cloud = await save_file_to_cloud(file_path=file_path)

    if not status_cloud:
        return

    # ищем файл в БД
    file = await search_file_in_db_by_path(file_path)
    # получаем дату изменения файла
    cur_edit_data_stamp = await asyncio.to_thread(os.path.getmtime, file_path)
    cur_edit_data = datetime.fromtimestamp(cur_edit_data_stamp)

    if not file:  # файл не найден в БД
        file = File(path=file_path, edit_data=cur_edit_data)
        logger.info(f"загружаю файл {file_name} в облако и БД")
    else:  # файл найден в БД
        file.edit_data = cur_edit_data
        logger.info(f"обновляю файл {file_name} в облаке и БД")

    # обновляю информацию о файе в БД
    async with async_session() as db:
        db.add(file)
        await db.commit()


async def delete_file_in_db(file_path: str):
    """Удаляет файл из БД"""
    file_name = file_path.split("/")[-1]
    file = await search_file_in_db_by_path(file_path)

    if not file:
        logger.error(f"при удалении файла {file_name} из БД, он не был найден")
        return

    async with async_session() as db:
        await db.delete(file)
        await db.commit()
    return True


async def sync_delete_file(file_path: str):
    """Удаляет файл из облака и БД"""
    file_name = file_path.split("/")[-1]

    db_file = await delete_file_in_db(file_path)
    cloud_file = await delete_file_in_cloud(file_path)

    if not db_file or not cloud_file:
        return

    logger.info(f"файл {file_name} удален из облака и БД")
