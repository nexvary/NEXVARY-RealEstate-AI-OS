from __future__ import annotations

import argparse
import os
import sys
import traceback
from pathlib import Path

from launcher import configure_runtime


def diagnostic_log_path() -> Path:
    override = os.environ.get("NEXVARY_SIDECAR_LOG")
    if override:
        return Path(override)
    local_app_data = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    return local_app_data / "Real Estate Business OS" / "Data" / "sidecar-boot.log"


def write_diagnostic(message: str) -> None:
    try:
        path = diagnostic_log_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(message.rstrip() + "\n")
    except Exception:
        pass


def main() -> None:
    parser = argparse.ArgumentParser(description="Real Estate Business OS local service")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--host", default="127.0.0.1")
    args = parser.parse_args()

    write_diagnostic("sidecar: boot")
    configure_runtime()
    os.environ["NEXVARY_NATIVE_SIDECAR"] = "1"
    write_diagnostic("sidecar: runtime configured")

    import uvicorn
    write_diagnostic("sidecar: uvicorn imported")
    from app.main import app as fastapi_app
    write_diagnostic("sidecar: FastAPI app imported")

    config = uvicorn.Config(
        fastapi_app,
        host=args.host,
        port=args.port,
        log_level="warning",
        access_log=False,
        use_colors=False,
        log_config=None,
    )
    server = uvicorn.Server(config)
    write_diagnostic(f"sidecar: serving {args.host}:{args.port}")
    server.run()


if __name__ == "__main__":
    try:
        main()
    except BaseException:
        write_diagnostic("sidecar: fatal exception\n" + traceback.format_exc())
        raise
