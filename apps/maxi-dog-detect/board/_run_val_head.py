import paramiko

# Minimal headless test: load 1 image, detect, print
code = r'''
from maix import image, nn
import os
MODEL="/root/models/dog_yolo11n/model_11523.mud"
d=nn.YOLO11(model=MODEL)
print("ok_load", d.input_width(), d.input_height(), d.labels)
path=None
for root, dirs, files in os.walk("/root/dog_db/detect"):
    for n in files:
        if n.lower().endswith(".jpg"):
            path=os.path.join(root,n)
            break
    if path: break
print("img", path)
img=image.load(path)
objs=d.detect(img, conf_th=0.5, iou_th=0.45)
print("n", len(objs))
for o in objs[:5]:
    print(d.labels[o.class_id], float(o.score), o.x, o.y, o.w, o.h)
print("DONE")
'''

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
with sftp.file("/tmp/val_one.py", "w") as f:
    f.write(code)
sftp.close()
stdin, stdout, stderr = c.exec_command("python /tmp/val_one.py", timeout=180)
print(stdout.read().decode(errors="replace"))
print(stderr.read().decode(errors="replace"))
c.close()
