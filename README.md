# PET AI MVP

강아지 CCTV 행동분석 MVP의 초기 골격입니다.

```text
Rust ingest → Python AI worker → Node.js API/WebSocket
                         ↘ PostgreSQL + Redis
```

## 실행

```bash
docker compose up --build
```

- API: http://localhost:3000/health
- AI worker: http://localhost:8001/health

## 영상 저장

`.env`에 Tapo 카메라의 RTSP 주소를 설정합니다.

```env
RTSP_URL=rtsp://camera_user:camera_password@192.168.0.10:554/stream1
```

이후 실행하면 `data/recordings/YYYY/MM/DD/` 아래에 60초 단위 MP4 파일이 저장됩니다.

```bash
docker compose up --build ingest
```

카메라 계정은 Tapo 앱에서 별도로 생성한 Camera Account를 사용해야 합니다.

현재 단계에서는 실제 RTSP 입력 대신 테스트용 프레임 이벤트를 받을 수 있는 API와 서비스 경계를 먼저 제공합니다.

## 전체 흐름 테스트

영상 파일을 `data/recordings/sample.mp4`에 둔 뒤 API가 AI Worker를 호출하도록 합니다.

```bash
curl -X POST http://localhost:3000/api/v1/inference \
  -H "content-type: application/json" \
  -d '{"cameraId":"tc70-01","framePath":"/data/recordings/sample.mp4"}'
curl http://localhost:3000/api/v1/events
```

컨테이너 내부 경로 기준으로 `framePath`를 전달해야 합니다. 현재는 OpenCV로 영상을 읽고 프레임 수를 계산하는 단계이며, 다음에 YOLO와 ByteTrack을 연결합니다.

## 다음 구현 순서

1. `apps/ingest-rs`에서 TC70 RTSP 수신 구현
2. AI worker에 YOLO 검출 및 ByteTrack 연결
3. PostgreSQL 이벤트 저장
4. React 대시보드 추가
5. Zone과 개체별 baseline 구현
