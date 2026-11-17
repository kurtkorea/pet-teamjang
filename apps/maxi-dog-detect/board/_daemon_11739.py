import paramiko
import time

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(
    "192.168.0.41",
    22,
    "root",
    "sipeed",
    timeout=20,
    banner_timeout=40,
    allow_agent=False,
    look_for_keys=True,
)

cmd = r"""
pkill -f '/root/detect_save.py' 2>/dev/null || true
sleep 1
mkdir -p /root/dog_db/detect/miss/20261116 /root/dog_db/detect/ok/20261116 /root/dog_db/detect/log/20261116
rm -f /root/dog_db/detect/log/20261116/detect_run.log
# detach from SSH session so process survives
setsid python -u /root/detect_save.py </dev/null >/root/dog_db/detect/log/20261116/detect_run.log 2>&1 &
echo PID:$!
sleep 8
ps w | grep detect_save | grep -v grep || echo NO_PROC
echo ===LOG===
tail -n 40 /root/dog_db/detect/log/20261116/detect_run.log
"""
stdin, stdout, stderr = c.exec_command(cmd, timeout=60)
print(stdout.read().decode())
err = stderr.read().decode()
if err.strip():
    print("ERR:", err)
c.close()
print("DONE")
