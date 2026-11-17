"""Upload 640x480 ONNX + best.pt + calib for MaixHub convert."""
from pathlib import Path

import paramiko

src = Path(r"D:\dev_pawkorea\pet-teamjang\apps\maxi-dog-detect\runs\dog-yolo11n\weights")
calib = Path(r"D:\dev_pawkorea\pet-teamjang\apps\maxi-dog-detect\runs\dog-yolo11n\maixhub_calib.zip")
remote_dir = "/root/models/dog_yolo11n/export"
files = [
    (src / "best.pt", f"{remote_dir}/best.pt"),
    (src / "best_640x480.onnx", f"{remote_dir}/best_640x480.onnx"),
]
if calib.is_file():
    files.append((calib, f"{remote_dir}/maixhub_calib.zip"))

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
c.exec_command(f"mkdir -p {remote_dir}")
sftp = c.open_sftp()
for local, rpath in files:
    print(f"upload {local.name} ({local.stat().st_size} bytes) -> {rpath}")
    sftp.put(str(local), rpath)
print("remote:")
for attr in sftp.listdir_attr(remote_dir):
    print(f"  {attr.filename} {attr.st_size}")
sftp.close()
c.close()
print("DONE")
