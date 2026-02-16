import logging
import os

from dotenv import load_dotenv

load_dotenv()

API_PORT = int(os.getenv("API_PORT", "5000"))
CAM_DEST = os.getenv("CAM_DEST", "~/")

logging.basicConfig(
    format=(
        "\033[90m%(asctime)s\033[0m [\033[36m%(levelname)s\033[0m] [\033[33m%(module)s::%(funcName)s\033[0m] %(message)s"
    ),
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
    handlers=[logging.StreamHandler()],
)
