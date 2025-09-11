import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


def env(key: str, default: str | None = None) -> str | None:
    return os.getenv(key, default)


def ensure_dir(p: str | Path) -> Path:
    path = Path(p)

    # parents= True will create parent directory if doesn't exist
    # exist_ok = True will not raise error even if file already exists
    path.mkdir(parents=True, exist_ok=True)
    return path


# print(env("CONFLUENCE_URL"))
# ensure_dir(env("INDEX_DIR", "./data/index"))
