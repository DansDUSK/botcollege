import gdown
import os
import re

GDRIVE_FOLDER_ID = "1VHwxwQMbrX7na1srshRRmr-le9iVgs1D"


def list_files_in_folder(folder_id: str) -> list[dict]:
    try:
        import subprocess
        import json

        result = subprocess.run(
            ["gdown", "--folder", f"https://drive.google.com/drive/folders/{folder_id}", "--json"],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            print(f"[gdrive] Ошибка gdown: {result.stderr}")
            return []

        files = json.loads(result.stdout)
        return files
    except Exception as e:
        print(f"[gdrive] Ошибка при получении списка файлов: {e}")
        return []


def download_pdf_by_name(filename: str, target_path: str) -> bool:
    try:
        files = list_files_in_folder(GDRIVE_FOLDER_ID)
        if not files:
            print("[gdrive] Не удалось получить список файлов")
            return False

        base_name = filename.replace(".pdf", "")

        target_file = None
        for f in files:
            file_name = f.get("path", "")
            if "/" in file_name:
                file_name = file_name.split("/")[-1]
            if file_name.startswith(base_name):
                target_file = f
                break

        if not target_file:
            print(f"[gdrive] Файл {filename} не найден в папке")
            print(f"[gdrive] Доступные файлы: {[f.get('path') for f in files]}")
            return False

        url = target_file.get("url")
        if not url:
            print(f"[gdrive] У файла {filename} нет URL")
            return False

        gdown.download(url, target_path, quiet=True)
        return os.path.exists(target_path) and os.path.getsize(target_path) > 0

    except Exception as e:
        print(f"[gdrive] Ошибка скачивания: {e}")
        return False
