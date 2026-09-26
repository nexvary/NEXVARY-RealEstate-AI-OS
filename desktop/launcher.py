from __future__ import annotations

import json
import os
import secrets
import socket
import sys
import threading
import time
import urllib.request
from pathlib import Path


APP_NAME = "NEXVARY RealEstate AI OS"
APP_DIR_NAME = "NEXVARY-RealEstate-AI-OS"


def resource_path(relative: str) -> Path:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
    return base / relative


def configure_runtime() -> tuple[Path, Path]:
    local_app_data = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    data_dir = local_app_data / "NEXVARY" / APP_DIR_NAME
    data_dir.mkdir(parents=True, exist_ok=True)

    secrets_file = data_dir / "runtime-secrets.json"
    if secrets_file.exists():
        try:
            values = json.loads(secrets_file.read_text(encoding="utf-8"))
        except Exception:
            values = {}
    else:
        values = {}

    jwt_secret = values.get("jwt_secret") or secrets.token_urlsafe(64)
    platform_admin_key = values.get("platform_admin_key") or secrets.token_urlsafe(48)
    values = {"jwt_secret": jwt_secret, "platform_admin_key": platform_admin_key}
    secrets_file.write_text(json.dumps(values, indent=2), encoding="utf-8")

    database_file = data_dir / "realestate.db"
    static_dir = resource_path("web")

    os.environ["APP_ENV"] = "desktop"
    os.environ["DATABASE_URL"] = f"sqlite:///{database_file.as_posix()}"
    os.environ["JWT_SECRET"] = jwt_secret
    os.environ["PLATFORM_ADMIN_KEY"] = platform_admin_key
    os.environ["NEXVARY_STATIC_DIR"] = str(static_dir)
    os.environ.setdefault("DEFAULT_LOCALE", "ar")

    return data_dir, static_dir


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def wait_for_server(url: str, timeout: float = 25.0) -> None:
    end = time.monotonic() + timeout
    last_error: Exception | None = None
    while time.monotonic() < end:
        try:
            with urllib.request.urlopen(f"{url}/health", timeout=1.2) as response:
                if response.status == 200:
                    return
        except Exception as exc:
            last_error = exc
        time.sleep(0.2)
    raise RuntimeError(f"Local service did not start in time: {last_error}")


def main() -> None:
    data_dir, static_dir = configure_runtime()
    if not static_dir.exists():
        raise RuntimeError(f"Bundled web UI is missing: {static_dir}")

    import uvicorn
    import webview
    from app.main import app as fastapi_app

    port = free_port()
    url = f"http://127.0.0.1:{port}"

    config = uvicorn.Config(
        fastapi_app,
        host="127.0.0.1",
        port=port,
        log_level="warning",
        access_log=False,
    )
    server = uvicorn.Server(config)
    server.install_signal_handlers = lambda: None

    thread = threading.Thread(target=server.run, name="nexvary-api", daemon=True)
    thread.start()
    wait_for_server(url)

    window = webview.create_window(
        APP_NAME,
        url=url,
        width=1440,
        height=900,
        min_size=(1024, 680),
        background_color="#050B13",
        text_select=True,
    )
    webview.start(debug=False, private_mode=False)
    server.should_exit = True
    thread.join(timeout=3)


if __name__ == "__main__":
    main()
