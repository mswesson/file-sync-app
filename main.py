import aiofiles
import os
import asyncio
from datetime import datetime
from typing import Optional, Tuple, List

from database.database import engine, async_session
from database.models import Base, File
from config_data.config import DIR_PATH
from sqlalchemy import select


async def search_file_in_db_by_path(path: str) -> Optional[File]:
    """Ищет файл в ДБ по пути"""
    async with async_session() as db:
        file_elem_db = await db.execute(select(File).where(File.path == path))
        file_elem_db = file_elem_db.scalar()
        return file_elem_db
    
    
async def add_or_edit_file_in_db(edit_data: datetime, path: str = None, file: File = None) -> None:
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
    edit_files_list = []
    files_by_dir = await asyncio.to_thread(os.listdir, path)
    
    for file_name in files_by_dir:
        file_path = os.path.join(path, file_name)
        if await asyncio.to_thread(os.path.isfile, file_path): # проверка на файл
            # добавляю путь файла в список найденных файлов
            files_list.append(file_path) 
            
            # получаю время изменения файла
            cur_edit_data_stamp = await asyncio.to_thread(os.path.getmtime, file_path)
            cur_edit_data = datetime.fromtimestamp(cur_edit_data_stamp)
            
            file_in_db = await search_file_in_db_by_path(file_path)
                
            if not file_in_db:
                await add_or_edit_file_in_db(path=file_path, edit_data=cur_edit_data)
                edit_files_list.append(file_path)
            elif not file_in_db.edit_data == cur_edit_data:
                await add_or_edit_file_in_db(file=file_in_db, edit_data=cur_edit_data)
                edit_files_list.append(file_path)
            
                
        elif await asyncio.to_thread(os.path.isdir, file_path): # проверка на директорию
            result_wraper = await search_files_to_dir(file_path)
            files_list.extend(result_wraper[0])
            edit_files_list.extend(result_wraper[1])
    
    return files_list, edit_files_list


async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    all_files, edit_files = await search_files_to_dir(DIR_PATH)
    deleted_files = await checking_remove_files(paths=all_files)
    print("Все файлы: ", all_files)
    print()
    print("Измененные файлы: ", edit_files)
    print()
    print("Удаленные файлы: ", deleted_files)  
        
        
if __name__ == "__main__":
    asyncio.run(main())
