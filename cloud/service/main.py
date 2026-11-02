"""Run the Zeus Cloud control plane locally: `python -m cloud.service`."""

from __future__ import annotations

import os

import uvicorn
from dotenv import load_dotenv

from .app import create_app
from .settings import Settings


def _load_env() -> None:
    from hermes_constants import get_hermes_home

    load_dotenv(get_hermes_home() / ".env", override=False)


def main() -> None:
    _load_env()
    settings = Settings.from_env()
    uvicorn.run(
        create_app(settings),
        host=os.getenv("ZEUS_CLOUD_HOST", "127.0.0.1"),
        port=int(os.getenv("ZEUS_CLOUD_PORT", "9121")),
        log_level=os.getenv("ZEUS_CLOUD_LOG_LEVEL", "info"),
    )


if __name__ == "__main__":
    main()
