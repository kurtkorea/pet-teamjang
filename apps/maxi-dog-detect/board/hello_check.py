"""MaixVision 연결/실행 최소 테스트. Run 후 터미널에 hello_ok 나오면 정상."""
print("hello_ok")
from maix import nn

detector = nn.YOLO11(model="/root/models/dog_yolo11n/model_11523.mud")
print("model_ok", detector.input_width(), detector.input_height(), detector.labels)
print("done")
