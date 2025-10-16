import os, uuid, shutil
from typing import Tuple

STORAGE_DIR = os.environ.get("IP_STORAGE_DIR", "data/uploads")

def save_upload(tmp_path: str, original_name: str) -> Tuple[str, str]:
    os.makedirs(STORAGE_DIR, exist_ok=True)
    ext = os.path.splitext(original_name)[1].lower()
    key = f"{uuid.uuid4().hex}{ext}"
    dest = os.path.join(STORAGE_DIR, key)
    shutil.copyfile(tmp_path, dest)
    return key, dest
