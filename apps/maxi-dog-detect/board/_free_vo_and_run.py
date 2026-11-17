"""Find/stop MaixCAM2 UI holder, then start detect_save.py."""
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

cmd = r"""
set -x
echo === maixapp ===
ls -la /maixapp/apps 2>/dev/null | head -40
echo === rc.local ===
cat /etc/rc.local 2>/dev/null | head -60
echo === python procs ===
ps auxww | grep -iE 'python|app|maix|launcher|ui' | grep -v grep
echo === stop holders ===
# common MaixCAM2 home / app manager names
for p in \
  '/maixapp' \
  'app_manager' \
  'apps_manager' \
  'launcher' \
  'settings' \
  'camera_app' \
  'detect_save' \
  'main.py'
do
  pkill -f "$p" 2>/dev/null || true
done
# stop any python using display/camera except our later start
pkill -f 'python .*/app.py' 2>/dev/null || true
sleep 2
# if home still holds VO via dedicated binary:
ls /maixapp/apps/*/app 2>/dev/null | head
for bin in /maixapp/apps/*/app; do
  [ -x "$bin" ] || continue
  pkill -f "$bin" 2>/dev/null || true
done
sleep 2
echo === remaining ===
ps auxww | grep -iE 'python|maixapp|/app' | grep -v grep || true
mkdir -p /root/dog_db/detect/miss/20261116 /root/dog_db/detect/ok/20261116 /root/dog_db/detect/log/20261116
rm -f /root/dog_db/detect/log/20261116/detect_run.log
nohup python /root/detect_save.py >/root/dog_db/detect/log/20261116/detect_run.log 2>&1 &
echo PID:$!
sleep 5
ps auxww | grep detect_save | grep -v grep || true
echo === log ===
tail -n 50 /root/dog_db/detect/log/20261116/detect_run.log
"""
stdin, stdout, stderr = c.exec_command(cmd)
print(stdout.read().decode())
err = stderr.read().decode()
if err.strip():
    print("ERR:", err[-2000:])
c.close()
