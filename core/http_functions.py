from typing import Optional

import aiofiles
import aiohttp

from config_data.config import DIR_PATH, TOKEN


async def get_upload_url(cloud_path: str) -> Optional[str]:
    """Получает ссылку на загрузку файла"""
    url = "https://cloud-api.yandex.net/v1/disk/resources/upload"
    headers = {"Authorization": f"OAuth {TOKEN}"}
    params = {
        "path": f"/file-sync-app/{cloud_path}",
        "overwrite": "true",
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url=url, headers=headers, params=params) as response:
            if response.status == 200:
                response_json = await response.json()
                upload_url = response_json.get("href")
                return upload_url


async def save_file_to_cloud(file_path: str):
    yandex_path = file_path.removeprefix(f"{DIR_PATH}/")
    count = 0
    while count < 5:
        upload_url = await get_upload_url(yandex_path)
        if upload_url:
            break
        else:
            await create_folder(yandex_path)
            count += 1
    else:
        raise ConnectionError("ошибка добавления папки")

    async with aiohttp.ClientSession() as session:
        async with aiofiles.open(file_path, "rb") as file_data:
            async with session.put(url=upload_url, data=file_data) as response:
                return response.status


async def create_folder(yandex_path: str):
    url = "https://cloud-api.yandex.net/v1/disk/resources"
    folders = yandex_path.split("/")[:-1]
    print(folders)
    headers = {
        "Authorization": f"OAuth {TOKEN}",
    }

    async with aiohttp.ClientSession() as session:
        path = ""
        for folder in folders:
            path += f"/{folder}"
            params = {
                "path": f"/file-sync-app{path}",
            }
            async with session.put(url, headers=headers, params=params) as response:
                if not response.status == 201:
                    print(f"папка {folder} уже существует, продолжаю работу")
                    continue


async def delete_file_in_cloud(file_path: str):
    """Удаляет файл из облака"""
    url = "https://cloud-api.yandex.net/v1/disk/resources"
    yandex_path = file_path.removeprefix(f"{DIR_PATH}/")
    print(yandex_path)
    headers = {
        "Authorization": f"OAuth {TOKEN}",
    }
    params = {"path": f"/file-sync-app/{yandex_path}", "permanently": "true"}
    async with aiohttp.ClientSession() as session:
        async with session.delete(url=url, headers=headers, params=params) as response:
            if response.status != 204:
                print(await response.json())
                raise ConnectionError("ошибка удаления файла")
            elif response.status == 204:
                print(f"файл {yandex_path} удален из облака")
    return True
