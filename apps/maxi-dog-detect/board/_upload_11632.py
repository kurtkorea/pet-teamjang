import time
from pathlib import Path

import paramiko

src = Path(
    r"D:\dev_pawkorea\pet-teamjang\apps\maxi-dog-detect\runs\dog-yolo11n\weights\maixhub-model-convert-maixcam2-11632_320"
)
script = Path(r"D:\dev_pawkorea\pet-teamjang\apps\maxi-dog-detect\board\detect_save.py")
remote = "/root/models/dog_yolo11n"
files = ["model_11632.mud", "model_11632_npu.axmodel", "model_11632_vnpu.axmodel"]

last = None
for attempt in range(1, 4):
    try:
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
        c.exec_command(f"mkdir -p {remote}")
        sftp = c.open_sftp()
        for name in files:
            local = src / name
            rpath = f"{remote}/{name}"
            print(f"upload {name} ({local.stat().st_size} bytes)")
            sftp.put(str(local), rpath)
        sftp.put(str(script), "/root/detect_save.py")
        print("upload detect_save.py")
        print("remote 11632:")
        for attr in sftp.listdir_attr(remote):
            if "11632" in attr.filename:
                print(f"  {attr.filename} {attr.st_size}")
        sftp.close()

        stdin, stdout, stderr = c.exec_command(f"cat {remote}/model_11632.mud")
        print(stdout.read().decode())

        verify = (
            "from maix import nn\n"
            "d=nn.YOLO11(model='/root/models/dog_yolo11n/model_11632.mud', dual_buff=False)\n"
            "print('ok', d.input_width(), d.input_height(), d.labels)\n"
        )
        with c.open_sftp().file("/tmp/verify_11632.py", "w") as f:
            f.write(verify)
        stdin, stdout, stderr = c.exec_command("python /tmp/verify_11632.py", timeout=120)
        print(stdout.read().decode())
        err = stderr.read().decode()
        if err.strip():
            print(err)
        c.close()
        print("DONE")
        break
    except Exception as e:
        last = e
        print(f"attempt {attempt} failed: {e}")
        time.sleep(3)
else:
    raise SystemExit(f"FAILED: {last}")
