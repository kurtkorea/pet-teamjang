"""Restart detect_save.py on MaixCAM2 after reboot; free camera/display first."""
import time

import paramiko

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

prep = r"""
echo === before ===
ps w | head -80
# stop common holders of camera/display
pkill -f '/root/detect_save.py' || true
pkill -f 'detect_save.py' || true
pkill -f 'main.py' || true
pkill -f 'app_launcher' || true
pkill -f 'launcher' || true
pkill -f 'maix_app' || true
pkill -f 'hello_maix' || true
sleep 2
mkdir -p /root/dog_db/detect/miss/20261116 /root/dog_db/detect/ok/20261116 /root/dog_db/detect/log/20261116
echo === after kill ===
ps w | grep -E 'detect|launcher|main.py|camera' | grep -v grep || true
"""
stdin, stdout, stderr = c.exec_command(prep)
print(stdout.read().decode())
print(stderr.read().decode())
time.sleep(2)

# start detect in background
start = (
    "nohup python /root/detect_save.py "
    ">/root/dog_db/detect/log/20261116/detect_run.log 2>&1 & "
    "echo PID:$!; sleep 4; "
    "ps w | grep detect_save | grep -v grep; "
    "echo === log ===; "
    "tail -n 40 /root/dog_db/detect/log/20261116/detect_run.log"
)
stdin, stdout, stderr = c.exec_command(start)
print(stdout.read().decode())
err = stderr.read().decode()
if err.strip():
    print(err)
c.close()
print("DONE")
