# maxi-dog-detect

MaixCAM2에서 모은 Detect 이미지(`F:\dog_db\detect`)와 `detect_log.csv`로  
**dog 박스를 자동 라벨**한 뒤 **CVAT(`maxi-dog-detect`)**에서 검수하고 YOLO11n을 학습합니다.

```text
F:\dog_db\detect\{ok,miss,log}
        → import-maix (CSV 박스 → YOLO 라벨)
        → cvat-push (프로젝트: maxi-dog-detect)
        → CVAT 검수
        → cvat-pull → train
```

## 준비

- Docker Desktop + CVAT (`apps\dog-detect\scripts\up-cvat.ps1`)
- Python 3.11+
- `dog-detect` 패키지 (형제 폴더)

```powershell
cd D:\dev_pawkorea\pet-teamjang\apps\maxi-dog-detect
Copy-Item .env.example .env
# .env에 CVAT 계정 입력 (dog-detect .env 와 동일해도 됨)
pip install -e ..\dog-detect
pip install -e .
```

## 1. Maix 데이터 → 자동 라벨

```powershell
python -m maxi_dog_detect import-maix
```

- `ok`/`miss` 이미지를 `F:\dog_db\detect\autolabel\images`에 링크/복사
- CSV의 dog 박스를 YOLO `labels/*.txt`로 변환
- cat / 박스 없음 → 빈 라벨 (검수에서 추가)

## 2. CVAT 업로드

```powershell
python -m maxi_dog_detect cvat-push
```

브라우저: http://localhost:8080 → 프로젝트 **maxi-dog-detect**

## 3. 검수 후 학습

```powershell
python -m maxi_dog_detect cvat-pull
python -m maxi_dog_detect train
```

결과: `runs\dog-yolo11n\weights\best.pt`

## 상태

```powershell
python -m maxi_dog_detect status
```
