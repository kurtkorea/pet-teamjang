from maix import camera, display, image, nn, app, time
import os

# detector = nn.YOLO11(model="/root/models/yolo11n.mud", dual_buff=False)

detector = nn.YOLO11(model="/root/models/dog_yolo11n/model_11739.mud", dual_buff=False)

TARGET_LABELS = {"dog"}
TARGET_IDS = {i for i, name in enumerate(detector.labels) if name in TARGET_LABELS}

# 모델 입력 640x480 (width x height)
CAM_W, CAM_H = 640, 480
cam = camera.Camera(CAM_W, CAM_H, detector.input_format())

# ---- 보드 저장 경로 (PC의 F:\dog_db\detect 와 같은 구조) ----
BASE_DIR = "/root/dog_db/detect"
MISS_DIR = BASE_DIR + "/miss/20261116"   # -> F:\dog_db\detect\miss
OK_DIR = BASE_DIR + "/ok/20261116"       # -> F:\dog_db\detect\ok
LOG_DIR = BASE_DIR + "/log/20261116"     # -> F:\dog_db\detect\log
LOG_FILE = LOG_DIR + "/detect_log.csv"

CONF_TH = 0.50           # 640 배포 후 재현율 확보 (청소기 hard-neg 반영분)
IOU_TH = 0.30
MERGE_IOU = 0.15
CONTAIN_TH = 0.45
CENTER_DIST_RATIO = 0.70
WEAK_SCORE = 0.35
HOLD_FRAMES = 10

OK_SCORE = 0.60          # 이 이상이면 성공 저장
SAVE_ENABLE = True       # True면 ok/miss 파일+CSV 저장, False면 화면만
SHOW = False              # False면 화면 없이 저장만 (VO 점유 시)
LOG_ENABLE = True        # True면 print 로그, False면 무음
SAVE_COOLDOWN_MS = 1000  # 같은 종류 저장 최소 간격 (디스크 폭주 방지)

disp = None
if SHOW:
    try:
        disp = display.Display()
    except Exception as e:
        print("display init failed, continue headless:", e)
        SHOW = False
        disp = None


def log(*args):
    if LOG_ENABLE:
        print(*args)


def ensure_dirs():
    for d in (MISS_DIR, OK_DIR, LOG_DIR):
        if not os.path.exists(d):
            os.makedirs(d)
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w") as f:
            f.write("ts_ms,kind,label,score,x,y,w,h,miss,path\n")


def area(box):
    return max(0, box[2]) * max(0, box[3])


def inter_area(a, b):
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    ax2, ay2 = ax + aw, ay + ah
    bx2, by2 = bx + bw, by + bh
    ix1 = max(ax, bx)
    iy1 = max(ay, by)
    ix2 = min(ax2, bx2)
    iy2 = min(ay2, by2)
    iw = max(0, ix2 - ix1)
    ih = max(0, iy2 - iy1)
    return iw * ih


def iou(a, b):
    inter = inter_area(a, b)
    if inter <= 0:
        return 0.0
    union = area(a) + area(b) - inter
    if union <= 0:
        return 0.0
    return inter / union


def containment(a, b):
    inter = inter_area(a, b)
    if inter <= 0:
        return 0.0
    m = min(area(a), area(b))
    if m <= 0:
        return 0.0
    return inter / m


def center_dist(a, b):
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    acx, acy = ax + aw * 0.5, ay + ah * 0.5
    bcx, bcy = bx + bw * 0.5, by + bh * 0.5
    dx = acx - bcx
    dy = acy - bcy
    return (dx * dx + dy * dy) ** 0.5


def same_target(a, b):
    if iou(a, b) >= MERGE_IOU:
        return True
    if containment(a, b) >= CONTAIN_TH:
        return True
    ref = max(min(a[2], a[3], b[2], b[3]), 1)
    return center_dist(a, b) <= ref * CENTER_DIST_RATIO


def merge_overlaps(dets):
    dets = sorted(dets, key=lambda d: d[4], reverse=True)
    kept = []
    for d in dets:
        drop = False
        for k in kept:
            if same_target(d[:4], k[:4]):
                drop = True
                break
            if d[4] < WEAK_SCORE and k[4] >= WEAK_SCORE:
                ref = max(min(k[2], k[3]), 1)
                if center_dist(d[:4], k[:4]) <= ref * 1.2:
                    drop = True
                    break
        if not drop:
            kept.append(d)
    return kept


def best_det(holds):
    if not holds:
        return None
    return max(holds, key=lambda d: d[4])


def write_log(ts_ms, kind, label, score, x, y, w, h, miss, path):
    with open(LOG_FILE, "a") as f:
        f.write(
            f"{ts_ms},{kind},{label},{score:.4f},{x},{y},{w},{h},{miss},{path}\n"
        )


def save_frame(img, kind, det):
    ts_ms = time.ticks_ms()
    if det is None:
        label, score, x, y, w, h, miss = "none", 0.0, 0, 0, 0, 0, 0
        fname = f"{kind}_{ts_ms}.jpg"
    else:
        x, y, w, h, score, label, miss = det
        fname = f"{kind}_{ts_ms}_{label}_{score:.2f}.jpg"

    out_dir = OK_DIR if kind == "ok" else MISS_DIR
    path = out_dir + "/" + fname
    img.save(path)
    write_log(ts_ms, kind, label, score, x, y, w, h, miss, path)
    log(f"saved {kind}: {path}")
    return ts_ms


if SAVE_ENABLE:
    ensure_dirs()
holds = []
last_ok_ms = 0
last_miss_ms = 0
last_kind = None

log("cam:", CAM_W, CAM_H)
log("model input:", detector.input_width(), detector.input_height())
log("labels:", detector.labels)
log("save enable:", SAVE_ENABLE)
log("log enable:", LOG_ENABLE)
log("save base:", BASE_DIR)
log("dog ids:", TARGET_IDS)

while not app.need_exit():
    img = cam.read()
    objs = detector.detect(img, conf_th=CONF_TH, iou_th=IOU_TH)

    cur = []
    for obj in objs:
        if obj.class_id not in TARGET_IDS:
            continue
        label = detector.labels[obj.class_id]
        cur.append([obj.x, obj.y, obj.w, obj.h, float(obj.score), label, 0])
    cur = merge_overlaps(cur)

    updated = []
    used = set()
    for h in holds:
        hx, hy, hw, hh, hs, hl, miss = h
        best_i = -1
        best_score = -1.0
        for i, c in enumerate(cur):
            if i in used:
                continue
            if same_target((hx, hy, hw, hh), c[:4]):
                if c[4] > best_score:
                    best_score = c[4]
                    best_i = i
        if best_i >= 0:
            x, y, w, hbox, score, label, _ = cur[best_i]
            updated.append([x, y, w, hbox, score, label, 0])
            used.add(best_i)
        else:
            miss += 1
            if miss <= HOLD_FRAMES:
                updated.append([hx, hy, hw, hh, hs, hl, miss])
    for i, c in enumerate(cur):
        if i not in used:
            updated.append(c)
    holds = merge_overlaps(updated)

    now = time.ticks_ms()
    det = best_det(holds)

    # 성공/실패 판정
    if det is not None and det[4] >= OK_SCORE and det[6] == 0:
        kind = "ok"
    else:
        kind = "miss"

    # 상태 전환이면 즉시 저장, 아니면 cooldown
    changed = (kind != last_kind)
    if SAVE_ENABLE:
        if kind == "ok":
            if changed or (now - last_ok_ms >= SAVE_COOLDOWN_MS):
                last_ok_ms = save_frame(img, "ok", det)
                last_kind = "ok"
        else:
            if changed or (now - last_miss_ms >= SAVE_COOLDOWN_MS):
                last_miss_ms = save_frame(img, "miss", det)
                last_kind = "miss"
    else:
        last_kind = kind

    # 화면 표시
    for x, y, w, hbox, score, label, miss in holds:
        img.draw_rect(x, y, w, hbox, color=image.COLOR_RED, thickness=1)
        tag = f"{label}:{score:.2f}"
        if miss > 0:
            tag += f" hold{miss}"
        img.draw_string(x, max(0, y - 16), tag, color=image.COLOR_RED)

    status = f"dogs={len(holds)} kind={last_kind} save={'on' if SAVE_ENABLE else 'off'}"
    img.draw_string(2, 2, status, color=image.COLOR_GREEN)
    if SHOW and disp is not None:
        disp.show(img)
