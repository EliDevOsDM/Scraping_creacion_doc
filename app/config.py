"""Módulo de configuración para el worker BCI."""

import random
import sys
from pathlib import Path
from enum import Enum


def _resolve_base_dir() -> Path:
    """Carpeta del .exe al empaquetar; carpeta del proyecto en desarrollo."""
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


BASE_DIR = _resolve_base_dir()


class WorkerConfig(Enum):
    """Enum para centralizar las constantes de configuración del worker."""
    USER_AGENTS = [
        # versiones de Chrome en Windows
        ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
         "Chrome/120.0.0.0 Safari/537.36"),
        ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
         "Chrome/123.0.0.0 Safari/537.36 Edg/123.0.2420.81"),
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
        ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
         "Chrome/120.0.0.0 Safari/537.36"),
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4; rv:124.0) Gecko/20100101 Firefox/124.0",
        ("Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/605.1.15 (KHTML, like Gecko) "
         "Version/17.4.1 Safari/605.1.15"),
        ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
         "Chrome/123.0.0.0 Safari/537.36"),
        "Mozilla/5.0 (X11; Linux i686; rv:124.0) Gecko/20100101 Firefox/124.0",
        ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
         "Chrome/140.0.0.0 Safari/537.36 Edg/141.0.3537.57"),
    ]
    BROWSER_CONTEXTS = [
        {
            "name": "desktop_pe",
            "viewport": {"width": 1920, "height": 1080},
            "locale": "es-PE",
            "timezone_id": "America/Lima"
        },
        {
            "name": "desktop_cl",
            "viewport": {"width": 1920, "height": 1080},
            "locale": "es-CL",
            "timezone_id": "America/Santiago"
        },
    ]
    DOWNLOAD_PATH = str(BASE_DIR / "files")
    SCREENSHOT_PATH = str(BASE_DIR / "screenshots")
    AUTOMATION_TIMEOUT_SECONDS = 180.0
    LOGIN_TIMEOUT_SECONDS = 15000
    ELEMENT_TIMEOUT_SECONDS = 20000
    MAIN_IFRAME_TIMEOUT_SECONDS = 15000

    @staticmethod
    def random_user_agent() -> str:
        return random.choice(WorkerConfig.USER_AGENTS.value)

    @staticmethod
    def random_browser_context() -> dict:
        return random.choice(WorkerConfig.BROWSER_CONTEXTS.value)
