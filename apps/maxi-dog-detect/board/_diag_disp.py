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
echo === ps ===
ps auxww 2>/dev/null | head -100 || ps w
echo === systemd ===
systemctl list-units --type=service --state=running 2>/dev/null | head -40 || true
echo === maix apps ===
ls /maixapp /root/apps /opt 2>/dev/null
ls /etc/init.d 2>/dev/null | head
echo === devices ===
ls -la /dev/fb* /dev/video* /dev/mmaix* 2>/dev/null | head -40
echo === last log ===
tail -n 30 /root/dog_db/detect/log/20261116/detect_run.log 2>/dev/null
"""
stdin, stdout, stderr = c.exec_command(cmd)
print(stdout.read().decode())
print(stderr.read().decode())
c.close()
