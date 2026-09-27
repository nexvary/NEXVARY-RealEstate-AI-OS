from __future__ import annotations

import argparse
import os
from pathlib import Path

from launcher import configure_runtime


def main() -> None:
    parser = argparse.ArgumentParser(description="NEXVARY RealEstate AI OS local API sidecar")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--host", default="127.0.0.1")
    args = parser.parse_args()

    configure_runtime()
    os.environ["NEXVARY_NATIVE_SIDECAR"] = "1"

    import uvicorn
    from app.main import app as fastapi_app

    config = uvicorn.Config(
        fastapi_app,
        host=args.host,
        port=args.port,
        log_level="warning",
        access_log=False,
    )
    server = uvicorn.Server(config)
    server.run()


if __name__ == "__main__":
    main()
