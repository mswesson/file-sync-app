from typing import Optional

import aiofiles
import aiohttp

from config_data.config import DIR_PATH, TOKEN
from logging_data.logger import logger


async def get_upload_url(cloud_path: str) -> Optional[str]:
    """Получение URL для загрузки файла в облако"""
    file_name = cloud_path.split("/")[-1]
    url = "https://cloud-api.yandex.net/v1/disk/resources/upload"
    headers = {"Authorization": f"OAuth {TOKEN}"}
    params = {
        "path": f"/file-sync-app/{cloud_path}",
        "overwrite": "true",
    }

    # делаем запрос к API Yandex для получения URL для загрузки
    async with aiohttp.ClientSession() as session:
        async with session.get(url=url, headers=headers, params=params) as response:
            status_code = response.status

            if status_code != 200:
                logger.error(
                    f"ошибка загрузки файла в облако {file_name} статус код {status_code}"
                )
                return

            response_json = await response.json()
            upload_url = response_json.get("href")
            return upload_url


async def save_file_to_cloud(file_path: str):
    """Загрузка файла в облако"""
    file_name = file_path.split("/")[-1]
    yandex_path = file_path.removeprefix(f"{DIR_PATH}/")

    # 5 попыток получить URL для загрузки файла в облако
    count = 0
    while count < 5:
        upload_url = await get_upload_url(yandex_path)

        if upload_url:
            break

        await create_folder(yandex_path)
        count += 1
    else:
        logger.error(
            "кол-во попыток на получение URL для загрузки файла в облако превышено"
        )
        return

    # отправляю файл в облако по URL полученом выше
    async with aiohttp.ClientSession() as session:
        async with aiofiles.open(file_path, "rb") as file_data:
            async with session.put(url=upload_url, data=file_data) as response:
                status_code = response.status

                if status_code != 201:
                    logger.error(
                        f"ошибка загрузки файла в облако {file_name} статус код {status_code}"
                    )
                    return
    return True


async def create_folder(yandex_path: str):
    """Создает попеременно папки, которые есть в пути"""
    url = "https://cloud-api.yandex.net/v1/disk/resources"
    folders = yandex_path.split("/")[:-1]
    headers = {"Authorization": f"OAuth {TOKEN}"}

    logger.info(f"создаю папки {folders} в облаке")

    # создаю попеременно каждую папку из списка папки
    async with aiohttp.ClientSession() as session:
        path = ""
        for folder in folders:
            path += f"/{folder}"
            params = {
                "path": f"/file-sync-app{path}",
            }
            async with session.put(url, headers=headers, params=params) as response:
                status_code = response.status
                if status_code != 201:
                    logger.debug(f"папка {folder} уже существует в облаке")
                    continue


async def delete_file_in_cloud(file_path: str):
    """Удаляет файл из облака"""
    file_name = file_path.split("/")[-1]
    url = "https://cloud-api.yandex.net/v1/disk/resources"
    yandex_path = file_path.removeprefix(f"{DIR_PATH}/")
    headers = {
        "Authorization": f"OAuth {TOKEN}",
    }
    params = {"path": f"/file-sync-app/{yandex_path}", "permanently": "true"}

    # делаю запрос к API Yandex на удаление файла
    async with aiohttp.ClientSession() as session:
        async with session.delete(url=url, headers=headers, params=params) as response:
            status_code = response.status

            if status_code != 204:
                logger.error(
                    f"файл {file_name} не был удален из облака, статус код {status_code}"
                )
                return
    return True
