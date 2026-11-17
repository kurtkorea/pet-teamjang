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
pkill -f '/root/detect_save.py' 2>/dev/null || true
sleep 1
python -u -c "print('py_ok')" 
which python
head -n 5 /root/detect_save.py
python -u /root/detect_save.py > /tmp/d11739.log 2>&1 &
PID=$!
echo PID:$PID
sleep 8
if kill -0 $PID 2>/dev/null; then echo ALIVE; else echo DEAD; fi
ps w | grep -E 'detect_save|python' | grep -v grep || true
echo ===LOG===
cat /tmp/d11739.log
wc -c /tmp/d11739.log
"""
stdin, stdout, stderr = c.exec_command(cmd, timeout=60)
print(stdout.read().decode())
err = stderr.read().decode()
if err.strip():
    print("ERR:", err)
c.close()
