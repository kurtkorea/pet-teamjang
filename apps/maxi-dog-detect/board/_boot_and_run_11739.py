"""Wait for board, ensure 11739 files, start detect headless-friendly."""
import time
from pathlib import Path

import paramiko

HOST = "192.168.0.41"
SRC = Path(
    r"D:\dev_pawkorea\pet-teamjang\apps\maxi-dog-detect\runs\dog-yolo11n\weights"
    r"\maixhub-model-convert-maixcam2-11739_640"
)
SCRIPT = Path(r"D:\dev_pawkorea\pet-teamjang\apps\maxi-dog-detect\board\detect_save.py")
REMOTE = "/root/models/dog_yolo11n"
FILES = ["model_11739.mud", "model_11739_npu.axmodel", "model_11739_vnpu.axmodel"]


def connect(retries=12):
    last = None
    for i in range(1, retries + 1):
        try:
            c = paramiko.SSHClient()
            c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            c.connect(
                HOST,
                22,
                "root",
                "sipeed",
                timeout=20,
                banner_timeout=40,
                allow_agent=False,
                look_for_keys=True,
            )
            return c
        except Exception as e:
            last = e
            print(f"connect {i}/{retries}: {e}")
            time.sleep(5)
    raise SystemExit(f"connect failed: {last}")


def run(c, cmd, timeout=60):
    stdin, stdout, stderr = c.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode()
    err = stderr.read().decode()
    return out, err


c = connect()
out, err = run(c, "uptime; ls -la /root/models/dog_yolo11n/model_11739* 2>&1; ls -la /root/detect_save.py 2>&1")
print(out)
if err.strip():
    print(err)

# re-upload if missing after reboot (usually persists)
need = "No such file" in out or "model_11739.mud" not in out
if need or "detect_save.py" not in out:
    print("re-uploading model/script")
    c.exec_command(f"mkdir -p {REMOTE}")
    sftp = c.open_sftp()
    for name in FILES:
        sftp.put(str(SRC / name), f"{REMOTE}/{name}")
        print("uploaded", name)
    sftp.put(str(SCRIPT), "/root/detect_save.py")
    print("uploaded detect_save.py")
    sftp.close()

# force headless in case VO held by launcher
script_txt = SCRIPT.read_text(encoding="utf-8")
if "SHOW = True" in script_txt:
    script_txt = script_txt.replace("SHOW = True", "SHOW = False", 1)
    SCRIPT.write_text(script_txt, encoding="utf-8")
    sftp = c.open_sftp()
    sftp.put(str(SCRIPT), "/root/detect_save.py")
    sftp.close()
    print("patched SHOW=False and re-uploaded script")

out, err = run(
    c,
    r"""
pkill -f '/root/detect_save.py' 2>/dev/null || true
sleep 1
mkdir -p /root/dog_db/detect/miss/20261116 /root/dog_db/detect/ok/20261116 /root/dog_db/detect/log/20261116
rm -f /tmp/d11739.log /root/dog_db/detect/log/20261116/detect_run.log
nohup python -u /root/detect_save.py >/root/dog_db/detect/log/20261116/detect_run.log 2>&1 &
echo PID:$!
sleep 8
ps w | grep detect_save | grep -v grep || echo NO_PROC
echo ===LOG===
tail -n 80 /root/dog_db/detect/log/20261116/detect_run.log || true
""",
    timeout=90,
)
print(out)
if err.strip():
    print(err)
c.close()
print("DONE")
