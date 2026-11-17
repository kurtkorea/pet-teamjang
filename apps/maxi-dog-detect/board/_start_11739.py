"""Start detect_save with model 11739 after freeing camera/display holders carefully."""
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

# Do not pkill '/maixapp' broadly — it can disrupt the session tooling.
prep = r"""
pkill -f '/root/detect_save.py' 2>/dev/null || true
pkill -f 'detect_save.py' 2>/dev/null || true
pkill -f '/maixapp/apps/launcher/launcher' 2>/dev/null || true
pkill -f '/maixapp/apps/camera' 2>/dev/null || true
pkill -f '/maixapp/apps/detector' 2>/dev/null || true
sleep 2
mkdir -p /root/dog_db/detect/miss/20261116 /root/dog_db/detect/ok/20261116 /root/dog_db/detect/log/20261116
rm -f /root/dog_db/detect/log/20261116/detect_run.log
ps w | grep -iE 'launcher|detect_save|camera' | grep -v grep || true
"""
stdin, stdout, stderr = c.exec_command(prep, timeout=30)
print(stdout.read().decode())
print(stderr.read().decode())
time.sleep(2)

start = (
    "nohup python /root/detect_save.py "
    ">/root/dog_db/detect/log/20261116/detect_run.log 2>&1 & "
    "echo PID:$!; sleep 6; "
    "ps w | grep detect_save | grep -v grep || echo NO_PROC; "
    "echo === log ===; "
    "tail -n 60 /root/dog_db/detect/log/20261116/detect_run.log || true"
)
stdin, stdout, stderr = c.exec_command(start, timeout=60)
print(stdout.read().decode())
err = stderr.read().decode()
if err.strip():
    print(err)
c.close()
print("DONE")
