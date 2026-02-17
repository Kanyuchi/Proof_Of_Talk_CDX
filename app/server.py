from __future__ import annotations

import os
import sys


def main() -> None:
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    try:
        import uvicorn
    except ModuleNotFoundError:
        print("Missing dependency: uvicorn")
        print("Install with: pip install -r requirements.txt")
        sys.exit(1)

    uvicorn.run("app.main:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    main()
