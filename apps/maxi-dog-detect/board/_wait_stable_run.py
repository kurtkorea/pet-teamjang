"""Wait until board uptime >= 3 minutes, then hold detect over SSH PTY."""
import sys
import time

import paramiko


def connect():
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
    return c


def uptime_seconds(c):
    i, o, e = c.exec_command("cat /proc/uptime", timeout=15)
    text = o.read().decode().strip().split()[0]
    return float(text)


# wait for stable boot
for n in range(1, 25):
    try:
        c = connect()
        sec = uptime_seconds(c)
        print(f"try {n}: uptime {sec:.0f}s", flush=True)
        if sec >= 180:
            break
        c.close()
    except Exception as ex:
        print(f"try {n}: {ex}", flush=True)
    time.sleep(15)
else:
    raise SystemExit("board never stayed up 3 minutes")

# do NOT kill launcher; just start detect headless
i, o, e = c.exec_command(
    "mkdir -p /root/dog_db/detect/miss/20261116 /root/dog_db/detect/ok/20261116 /root/dog_db/detect/log/20261116; "
    "ls -la /root/models/dog_yolo11n/model_11739.mud /root/detect_save.py",
    timeout=20,
)
print(o.read().decode(), flush=True)

transport = c.get_transport()
chan = transport.open_session()
chan.get_pty()
chan.exec_command(
    "python -u /root/detect_save.py 2>&1 | tee -a /root/dog_db/detect/log/20261116/detect_run.log"
)
print("detect channel open", flush=True)
deadline = time.time() + 40
got = False
while time.time() < deadline:
    if chan.recv_ready():
        chunk = chan.recv(4096)
        sys.stdout.buffer.write(chunk)
        sys.stdout.flush()
        if b"cam:" in chunk or b"saved" in chunk:
            got = True
            break
    if chan.exit_status_ready():
        print("exit", chan.recv_exit_status(), flush=True)
        break
    time.sleep(0.3)

print("\nGOT_CAM" if got else "\nNO_CAM_YET", flush=True)
print("holding...", flush=True)
while not chan.exit_status_ready():
    if chan.recv_ready():
        chan.recv(8192)
    time.sleep(3)
print("ended", chan.recv_exit_status())
