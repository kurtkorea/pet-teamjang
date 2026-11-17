import paramiko
from pathlib import Path

local = Path(__file__).with_name("val_from_files.py")
remote_script = "/root/val_from_files.py"

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
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
sftp = c.open_sftp()
sftp.put(str(local), remote_script)
sftp.close()

cmd = (
    "ls -la /root/val_from_files.py /root/models/dog_yolo11n/model_11523.mud; "
    "echo ---dirs---; "
    "ls -ld /root/dog_db/detect /root/dog_db/detect/miss /root/dog_db/detect/ok "
    "/root/dog_db/detect/miss/20261111 /root/dog_db/detect/ok/20261111 2>/dev/null; "
    "echo ---counts---; "
    "find /root/dog_db/detect -type f \\( -name '*.jpg' -o -name '*.jpeg' -o -name '*.png' \\) 2>/dev/null | wc -l"
)
stdin, stdout, stderr = c.exec_command(cmd)
print(stdout.read().decode())
err = stderr.read().decode()
if err:
    print(err)
c.close()
print("UPLOADED", remote_script)
