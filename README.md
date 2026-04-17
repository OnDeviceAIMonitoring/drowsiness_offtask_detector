# On-Device Drowsiness & Off-Task Monitoring

MediaPipe + OpenCV 기반의 온디바이스 졸음·산만함·딴 짓 감지 시스템.  
Raspberry Pi 환경에서 카메라 1대로 '졸음'·'산만함'·'Off-Task' Detector 동시에 실행

---

## 파일 구성

```
signal_hub.py              # 메인 실행 파일 — Detector 통합 오케스트레이터
config/
  off_task.json            # Off-Task 감지기 설정 (모델, 임계값, 시각화 등)
models/
  yolo26n.onnx             # YOLO ONNX 모델 (핸드폰/물체 감지용, 직접 배치)
detectors/
  base.py                  # Signal 데이터클래스 + BaseDetector 인터페이스
  drowsiness.py            # 졸음 감지 (EAR + 고개 pitch 기반)
  fidget.py                # 산만함 감지 (동작 에너지 burst 기반)
  off_task.py              # Off-Task 감지 (Holistic + YOLO ONNX 복합)
  off_task_viz.py           # Off-Task 시각화 모듈
```

---
## 환경

Raspberry PI 의 env 가상환경 그대로 사용

### 추가 패키지 (Off-Task 감지기)

```bash
pip install onnxruntime     # 핸드폰/물체 감지용 (선택)
```

## 실행

```bash
python signal_hub.py
```

종료: `q` 키

---

## 알고리즘 요약

### 졸음 감지 (`drowsiness.py`)
- **경로 A** (얼굴 보임): EAR(Eye Aspect Ratio)이 캘리브레이션 임계값 이하로 ~1.8초 지속 → 졸음
- **경로 B** (얼굴 안 보임): Pose pitch로 고개 숙임 3초 지속 → 졸음

### 산만함 감지 (`fidget.py`)
- 코·어깨·팔꿈치 5개 키포인트의 프레임 간 이동량(motion energy) 측정
- 정상 대비 4배 이상 이동이 0.8초 지속 → burst 1회
- 30초 안에 burst 4회 이상 → LOW FOCUS

### 딴 짓 감지 (`off_task.py`)
MediaPipe Holistic + YOLO ONNX 기반 딴 짓 감지. 아래 조건 중 하나라도 해당하면 `OFF_TASK` 시그널 발생:

- **핸드폰/물체 사용**: YOLO ONNX로 핸드폰 등 물체 감지 + 손과 접촉 여부 확인  
  → 슬라이딩 윈도우 방식: N초(`phone_window_seconds`) 안에 X번(`phone_hit_threshold`) 이상 감지 시 알림 (깜빡임 억제)
- **머리 방향(Yaw) 이탈**: Face Mesh yaw가 캘리브레이션 기준에서 ±30° 이상 벗어남  
  → 슬라이딩 윈도우 방식: N초(`yaw_window_seconds`) 안에 X번(`yaw_hit_threshold`) 이상 감지 시 알림
- **얼굴 트래커 이탈**: Kalman Filter 기반 트래커가 화면 밖을 N초(`tracker_out_seconds`) 이상 연속 추적 시 알림
- **손 미감지**: 손이 화면에서 사라지거나 책상 아래로 내려감
- **웃음·대화 감지**: 입 비율 + 입 움직임 표준편차 기반
- **자동 캘리브레이션**: 시작 후 3초간 정면 yaw 기준값 자동 설정

좌측 하단에 산만함(fidget) 바와 유사한 딴 짓 상태 바가 표시됩니다 (핸드폰 / Yaw 슬라이딩 윈도우 게이지).

<!-- #### 설정 (`config/off_task.json`)

| 섹션 | 설명 |
|------|------|
| `model` | ONNX 모델 경로, 감지 라벨, 스코어 임계값 |
| `mediapipe` | Holistic confidence 설정 |
| `thresholds` | 각종 감지 임계값 (yaw, 손, 트래커, 대화 등) |
| `tracking` | Kalman 트래커 파라미터 |
| `calibration` | 자동 캘리브레이션 설정 (시간, 최소 샘플) |
| `features` | 개별 감지 기능 on/off |
| `visualization` | 시각화 요소 개별 on/off (`draw_landmarks`, `draw_ui_panel`, `draw_tracker_history`, `draw_phone_boxes`) |

YOLO ONNX 모델은 `models/` 폴더에 배치해야 합니다.  
`onnxruntime` 미설치 또는 모델 파일 미존재 시 객체 감지 기능만 비활성화되고 나머지는 정상 동작합니다. -->

---

## 새 Detector 추가 방법

1. `detectors/` 에 `BaseDetector` 상속 클래스 작성
2. `process_frame()`, `draw_hud()`, `release()` 구현
3. `signal_hub.py`의 `DETECTORS` 리스트에 추가

---

## 시그널 출력 연동

`signal_hub.py`의 `on_signals()` 함수에서 `Signal` 객체를 수신

| 시그널 | 소스 | 설명 |
|--------|------|------|
| `DROWSINESS` | drowsiness | 졸음 감지 |
| `LOW_FOCUS` | fidget | 산만함(반복 움직임) 감지 |
| `OFF_TASK` | off_task | 딴 짓 감지 (핸드폰, 시선, 손 등) |

gui 에 signal 출력
