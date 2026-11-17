"""보드 저장 이미지로 model_11523 검증 (카메라 없음).

MaixVision에서 실행하거나:
  python /root/val_from_files.py
"""
from maix import image, nn, display, app, time
import os

MODEL = "/root/models/dog_yolo11n/model_11523.mud"
# 검증할 폴더 (없으면 자동으로 건너뜀)
SCAN_DIRS = [
    "/root/dog_db/detect/miss/20261111",
    "/root/dog_db/detect/ok/20261111",
    "/root/dog_db/detect/miss",
    "/root/dog_db/detect/ok",
]
OUT_CSV = "/root/dog_db/detect/log/val_11523.csv"
CONF_TH = 0.50
IOU_TH = 0.45
MAX_IMAGES = 50           # 0이면 제한 없음 (MaixVision은 처음 50장 권장)
SHOW = False              # True면 화면 표시(메모리/충돌 가능). MaixVision은 False 권장
DELAY_MS = 30             # SHOW=True 일 때만

IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".bmp")


def list_images(dirs):
    seen = set()
    files = []
    for d in dirs:
        if not os.path.isdir(d):
            continue
        for root, _dirs, names in os.walk(d):
            for name in names:
                low = name.lower()
                if not low.endswith(IMAGE_EXTS):
                    continue
                path = os.path.join(root, name)
                if path in seen:
                    continue
                seen.add(path)
                files.append(path)
    files.sort()
    return files


detector = nn.YOLO11(model=MODEL)
disp = display.Display() if SHOW else None
paths = list_images(SCAN_DIRS)
if MAX_IMAGES > 0:
    paths = paths[:MAX_IMAGES]

print("model:", MODEL)
print("input:", detector.input_width(), detector.input_height())
print("labels:", detector.labels)
print("images:", len(paths))
print("conf:", CONF_TH)

os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
with open(OUT_CSV, "w") as f:
    f.write("path,n_dog,best_score,x,y,w,h\n")

total = 0
with_dog = 0
scores = []

for path in paths:
    if app.need_exit():
        break
    try:
        img = image.load(path)
    except Exception as e:
        print("load fail:", path, e)
        continue

    objs = detector.detect(img, conf_th=CONF_TH, iou_th=IOU_TH)
    dogs = []
    for obj in objs:
        name = detector.labels[obj.class_id]
        if name != "dog":
            continue
        dogs.append((float(obj.score), obj.x, obj.y, obj.w, obj.h))
        if SHOW:
            img.draw_rect(obj.x, obj.y, obj.w, obj.h, color=image.COLOR_RED, thickness=2)
            img.draw_string(obj.x, max(0, obj.y - 16), f"dog:{obj.score:.2f}", color=image.COLOR_RED)

    total += 1
    if dogs:
        with_dog += 1
        dogs.sort(reverse=True)
        best = dogs[0]
        scores.append(best[0])
        line = f"{path},{len(dogs)},{best[0]:.4f},{best[1]},{best[2]},{best[3]},{best[4]}\n"
    else:
        line = f"{path},0,0,0,0,0,0\n"

    with open(OUT_CSV, "a") as f:
        f.write(line)

    tag = f"{total}/{len(paths)} dogs={len(dogs)}"
    if dogs:
        tag += f" best={dogs[0][0]:.2f}"
    print(tag, path)
    if SHOW and disp is not None:
        img.draw_string(2, 2, tag, color=image.COLOR_GREEN)
        disp.show(img)
        time.sleep_ms(DELAY_MS)

avg = (sum(scores) / len(scores)) if scores else 0.0
print("---")
print("done:", total)
print("with_dog:", with_dog)
print("no_dog:", total - with_dog)
print("avg_best_score:", round(avg, 4))
print("csv:", OUT_CSV)
