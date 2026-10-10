import requests
from urllib.parse import urlencode
from config import YADISK_PUBLIC_URL


def download_pdf_by_name(filename: str, target_path: str) -> bool:
    try:
        meta_url = "https://cloud-api.yandex.net/v1/disk/public/resources/download?" + urlencode({
            "public_key": YADISK_PUBLIC_URL,
            "path": f"/{filename}",
        })
        resp = requests.get(meta_url, timeout=15)
        if resp.status_code != 200:
            print(f"[yadisk] Ошибка API: {resp.status_code} {resp.text}")
            return False

        href = resp.json().get("href")
        if not href:
            print(f"[yadisk] Нет ссылки для {filename}")
            return False

        file_resp = requests.get(href, timeout=60)
        if file_resp.status_code != 200:
            print(f"[yadisk] Ошибка скачивания: {file_resp.status_code}")
            return False

        with open(target_path, "wb") as f:
            f.write(file_resp.content)
        return True

    except Exception as e:
        print(f"[yadisk] Исключение: {e}")
        return False