import os
import re
import zipfile

import requests

download_filename = "chrome_driver.zip"
version = open("version.txt", "r").read().strip()

def get_last_chrome_driver_version():
    url = "https://chromedriver.storage.googleapis.com/?delimiter=/&prefix="
    response = requests.get(url)
    ver = str(open("version.txt", "r").read())
    version = re.search(f"{ver}\.\d+\.\d+\.\d+", response.text).group(0)
    return version


def download_file(url, filename):
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    return filename


def download_chrome_driver(version):
    print(f"Скачивание chromedriver v. {version}")
    url = f"https://chromedriver.storage.googleapis.com/{version}/chromedriver_win32.zip"
    download_file(url, download_filename)
    print(f"Успешно скачен chromedriver v. {version}")


def upzip_file(filepath, upzip_to):
    with zipfile.ZipFile(filepath, 'r') as zip_ref:
        zip_ref.extractall(upzip_to)
    os.remove(download_filename)


# get_full_version(101) -> '101.0.4951.41'
def get_full_version(version: int):
    print(f"Поиск chromedriver v. {version}")
    response = requests.get(f"https://chromedriver.storage.googleapis.com/LATEST_RELEASE_{version}")
    return response.text


download_chrome_driver(get_full_version(version))
upzip_file("chrome_driver.zip", "./")

