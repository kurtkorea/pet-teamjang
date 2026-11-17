"""Try download MaixHub convert zip 11739 using Chrome cookies."""
from __future__ import annotations

import os
import shutil
import sqlite3
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

OUT = Path(
    r"D:\dev_pawkorea\pet-teamjang\apps\maxi-dog-detect\runs\dog-yolo11n\weights"
    r"\maixhub-model-convert-maixcam2-11739.zip"
)
URLS = [
    "https://maixhub.com/toolbox/convert/maixcam/11739/download",
    "https://www.maixhub.com/toolbox/convert/maixcam/11739/download",
    "https://maixhub.com/api/v1/modelConvert/result/11739",
    "https://maixhub.com/api/v1/modelConvert/11739/download",
    "https://www.maixhub.com/api/v1/modelConvert/11739/download",
]


def load_cookies() -> str:
    local = Path(os.environ["LOCALAPPDATA"]) / "Google" / "Chrome" / "User Data" / "Default"
    candidates = [local / "Network" / "Cookies", local / "Cookies"]
    tmp = Path(tempfile.mkdtemp()) / "Cookies"
    last_err: Exception | None = None
    for src in candidates:
        if not src.is_file():
            continue
        try:
            shutil.copy2(src, tmp)
            break
        except Exception as e:  # noqa: BLE001
            last_err = e
    else:
        raise SystemExit(f"cannot copy chrome cookies: {last_err}")

    conn = sqlite3.connect(str(tmp))
    rows = conn.execute(
        "select host_key, name, value from cookies where host_key like '%maixhub%'"
    ).fetchall()
    conn.close()
    print(f"maixhub cookies: {len(rows)}")
    return "; ".join(f"{n}={v}" for _, n, v in rows)


def main() -> None:
    cookie = load_cookies()
    for url in URLS:
        req = urllib.request.Request(
            url,
            headers={
                "Cookie": cookie,
                "User-Agent": "Mozilla/5.0",
                "Referer": "https://maixhub.com/toolbox/convert/maixcam/11739",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                ctype = resp.headers.get("content-type", "")
                data = resp.read()
                print(url, "->", resp.status, ctype, "bytes", len(data))
                if len(data) > 100_000 and (
                    "zip" in ctype or data[:2] == b"PK" or "octet" in ctype
                ):
                    OUT.write_bytes(data)
                    print("saved", OUT, OUT.stat().st_size)
                    return
                print("skip body head", data[:80])
        except Exception as e:  # noqa: BLE001
            print(url, "->", type(e).__name__, e)
    raise SystemExit("download failed")


if __name__ == "__main__":
    main()
