import paramiko
import sys

cmds = [
    "uname -a",
    "ls -la /root/val_from_files.py /root/models/dog_yolo11n/model_11523.mud /root/models/dog_yolo11n/model_11523_npu.axmodel /root/models/dog_yolo11n/model_11523_vnpu.axmodel 2>&1",
    "which python; python --version 2>&1; ls /usr/bin/python* 2>&1 | head",
    "free -m; df -h /root | tail -1",
    "ps aux | head -20",
]

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    c.connect(
        "192.168.0.41",
        port=22,
        username="root",
        password="sipeed",
        timeout=20,
        banner_timeout=30,
        allow_agent=False,
        look_for_keys=True,
    )
except Exception as e:
    print("SSH_CONNECT_FAIL:", e)
    sys.exit(1)

for cmd in cmds:
    print("====", cmd)
    stdin, stdout, stderr = c.exec_command(cmd, timeout=30)
    out = stdout.read().decode(errors="replace")
    err = stderr.read().decode(errors="replace")
    print(out)
    if err.strip():
        print("ERR:", err)

# try short maix import
print("==== python import maix")
stdin, stdout, stderr = c.exec_command(
    "python -c \"from maix import nn, image; print('maix_ok'); d=nn.YOLO11(model='/root/models/dog_yolo11n/model_11523.mud'); print('labels', d.labels); print('size', d.input_width(), d.input_height())\"",
    timeout=120,
)
print(stdout.read().decode(errors="replace"))
print(stderr.read().decode(errors="replace"))
c.close()
