import paramiko

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
for cmd in [
    "uptime",
    "ps w | grep -E 'detect_save|python' | grep -v grep || echo NO_PY",
    "wc -c /root/dog_db/detect/log/20261116/detect_run.log /tmp/d11739.log 2>&1",
    "tail -n 100 /root/dog_db/detect/log/20261116/detect_run.log 2>&1",
    "grep -n SHOW /root/detect_save.py | head",
]:
    print("===", cmd)
    i, o, e = c.exec_command(cmd, timeout=30)
    print(o.read().decode())
    err = e.read().decode()
    if err.strip():
        print("ERR", err)
c.close()
