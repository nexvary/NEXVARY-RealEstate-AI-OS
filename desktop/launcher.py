from __future__ import annotations

import json
import shutil
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
SCHEMA_GENERATION = "v1.7"


def resource_path(relative: str) -> Path:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
    return base / relative


def archive_incompatible_development_database(data_dir: Path) -> None:
    marker_file = data_dir / "development-profile.json"
    database_file = data_dir / "realestate.db"
    if not marker_file.exists() or not database_file.exists():
        return
    try:
        state = json.loads(marker_file.read_text(encoding="utf-8"))
    except Exception:
        state = {}
    if not state.get("enabled"):
        return
    previous = str(state.get("schema_generation") or "")
    if previous == SCHEMA_GENERATION:
        return

    backup_dir = data_dir / "development-backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    target = backup_dir / f"realestate-{previous or 'legacy'}-{stamp}.db"
    shutil.move(str(database_file), str(target))
    for suffix in ("-wal", "-shm"):
        sidecar = Path(str(database_file) + suffix)
        if sidecar.exists():
            shutil.move(str(sidecar), str(backup_dir / f"{target.name}{suffix}"))
    state["schema_generation"] = SCHEMA_GENERATION
    marker_file.write_text(json.dumps(state, indent=2), encoding="utf-8")


def configure_runtime() -> tuple[Path, Path]:
    local_app_data = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    data_dir = local_app_data / "NEXVARY" / APP_DIR_NAME
    data_dir.mkdir(parents=True, exist_ok=True)
    archive_incompatible_development_database(data_dir)

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
    integration_master_secret = values.get("integration_master_secret") or secrets.token_urlsafe(64)
    values = {
        "jwt_secret": jwt_secret,
        "platform_admin_key": platform_admin_key,
        "integration_master_secret": integration_master_secret,
    }
    secrets_file.write_text(json.dumps(values, indent=2), encoding="utf-8")

    database_file = data_dir / "realestate.db"
    static_dir = resource_path("web")

    os.environ["APP_ENV"] = "desktop"
    os.environ["DATABASE_URL"] = f"sqlite:///{database_file.as_posix()}"
    os.environ["JWT_SECRET"] = jwt_secret
    os.environ["PLATFORM_ADMIN_KEY"] = platform_admin_key
    os.environ["INTEGRATION_MASTER_SECRET"] = integration_master_secret
    os.environ["NEXVARY_STATIC_DIR"] = str(static_dir)
    os.environ["NEXVARY_DATA_DIR"] = str(data_dir)
    os.environ["NEXVARY_SCHEMA_GENERATION"] = SCHEMA_GENERATION
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
