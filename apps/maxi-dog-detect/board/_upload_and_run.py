"""Upload detect_save.py and start it on the board."""
import time
from pathlib import Path

import paramiko

script = Path(r"D:\dev_pawkorea\pet-teamjang\apps\maxi-dog-detect\board\detect_save.py")

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(
    "192.168.0.41",
    22,
    "root",
    "sipeed",
    timeout=20,
    banner_timeout=30,
    allow_agent=False,
    look_for_keys=True,
)

# free common holders
free = r"""
pkill -f detect_save.py || true
pkill -f '/maixapp/apps' || true
for bin in /maixapp/apps/*/app; do [ -x "$bin" ] && pkill -f "$bin" || true; done
sleep 2
mkdir -p /root/dog_db/detect/miss/20261116 /root/dog_db/detect/ok/20261116 /root/dog_db/detect/log/20261116
"""
c.exec_command(free)
time.sleep(2)

sftp = c.open_sftp()
sftp.put(str(script), "/root/detect_save.py")
print("uploaded detect_save.py")
sftp.close()

start = (
    "rm -f /root/dog_db/detect/log/20261116/detect_run.log; "
    "nohup python /root/detect_save.py "
    ">/root/dog_db/detect/log/20261116/detect_run.log 2>&1 & "
    "echo PID:$!; sleep 6; "
    "ps auxww | grep detect_save | grep -v grep; "
    "echo === log ===; "
    "tail -n 60 /root/dog_db/detect/log/20261116/detect_run.log"
)
stdin, stdout, stderr = c.exec_command(start)
print(stdout.read().decode())
err = stderr.read().decode()
if err.strip():
    print(err)
c.close()
print("DONE")
