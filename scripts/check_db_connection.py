from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.db import backend_summary, init_db


def main() -> None:
    info = backend_summary()
    init_db()
    print("Database check passed")
    print(f"Backend: {info['backend']}")
    print(f"URL: {info['database_url']}")


if __name__ == "__main__":
    main()
