import json

import requests
from .helper import project_dir, skip_function_if_env
from loguru import logger

TRANSLATION_FILE = project_dir / "data" / "translations.json"


@skip_function_if_env("SKIP_TRANSLATIONS")
def save_translations_json(indent: int = 4):
    logger.debug("Saving Translations")
    with open(TRANSLATION_FILE, "w") as file:
        json.dump(
            requests.get("https://api.gametools.network/bf2042/translations/").json(),
            file,
            indent=indent,
        )
    return True


if __name__ == "__main__":
    save_translations_json()
