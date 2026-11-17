"""Keep detect_save running over an SSH PTY (survives as long as this process lives)."""
import sys
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
    banner_timeout=40,
    allow_agent=False,
    look_for_keys=True,
)

# cleanup old
c.exec_command("pkill -f '/root/detect_save.py' 2>/dev/null || true")
time.sleep(1)

transport = c.get_transport()
chan = transport.open_session()
chan.get_pty(term="xterm", width=120, height=40)
chan.exec_command(
    "mkdir -p /root/dog_db/detect/log/20261116; "
    "python -u /root/detect_save.py 2>&1 | tee /root/dog_db/detect/log/20261116/detect_run.log"
)
print("channel started; holding SSH PTY", flush=True)
# stream a bit of startup then keep alive
deadline = time.time() + 15
buf = b""
while time.time() < deadline:
    if chan.recv_ready():
        chunk = chan.recv(4096)
        if not chunk:
            break
        sys.stdout.buffer.write(chunk)
        sys.stdout.flush()
        buf += chunk
    elif chan.exit_status_ready():
        print("\nEXIT early", chan.recv_exit_status(), flush=True)
        break
    else:
        time.sleep(0.2)

if b"cam:" in buf or b"model input" in buf:
    print("\n=== STARTUP_OK; holding process ===", flush=True)
else:
    print("\n=== startup unclear; still holding ===", flush=True)

# hold forever until killed
while not chan.exit_status_ready():
    if chan.recv_ready():
        chunk = chan.recv(4096)
        if chunk:
            # keep log growing via tee already; don't spam console
            pass
    time.sleep(2)
print("detect exited", chan.recv_exit_status())
c.close()
