# On-Device Drowsiness & Fidget Monitoring

MediaPipe + OpenCV 기반의 온디바이스 졸음 및 산만함 감지 시스템.  
Raspberry Pi 환경에서 카메라 1대로 '졸음'&'산만함' Detector 동시에 실행

---

## 파일 구성

```
signal_hub.py           # 메인 실행 파일 — Detector 통합 오케스트레이터
detectors/
  base.py               # Signal 데이터클래스 + BaseDetector 인터페이스
  drowsiness.py         # 졸음 감지 (EAR + 고개 pitch 기반)
  fidget.py             # 산만함 감지 (동작 에너지 burst 기반)
```

---

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

---

## 새 Detector 추가 방법

1. `detectors/` 에 `BaseDetector` 상속 클래스 작성
2. `process_frame()`, `draw_hud()`, `release()` 구현
3. `signal_hub.py`의 `DETECTORS` 리스트에 추가

---

## 시그널 출력 연동

`signal_hub.py`의 `on_signals()` 함수에서 `Signal` 객체를 수신

gui 에 signal 출력