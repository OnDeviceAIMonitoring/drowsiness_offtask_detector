# On-Device AI Behavior Monitor

MediaPipe + OpenCV 기반 온디바이스 행동 감지 통합 관리 시스템.  
`signal_hub.py` 를 중심으로 `detectors/` 하위에 Detector 추가해 나가는 구조
Raspberry Pi + USB/CSI 카메라 환경에서 실행됩니다.

---

## Detector 개발 현황

| 상태 | Detector | 파일 | 시그널 | 감지 방식 |
|:----:|----------|------|--------|----------|
| ✅ | 졸음 감지 | `drowsiness.py` | `DROWSINESS` | EAR + Face·Pose pitch |
| ✅ | 하트 제스처 | `heart.py` | `HEART` | 양손 검지·엄지 형태 분석 |
| ✅ | 딴짓 - 산만함 감지 | `fidget.py` | `LOW_FOCUS` | Motion energy burst 반복 |
| 🔲 | 딴짓 통합 - 객체탐지/tracking/웃으면서대화 | `-` | `-` | - |
| 🔲 | (추가 예정) | — | — | — |

---

## 파일 구성

```
signal_hub.py            # 메인 실행 파일 — 모든 Detector 통합 오케스트레이터
detectors/
  base.py                # Signal 데이터클래스 + BaseDetector 인터페이스 (공통)
  drowsiness.py          # 졸음 감지
  fidget.py              # 산만함(반복 움직임) 감지
  heart.py               # 하트 제스처 감지
  (추가 예정...)          # 새 감지기는 이 폴더에 추가
```

---

## 환경

Raspberry PI 의 `env` 가상환경 그대로 사용

---

## 실행

```bash
python signal_hub.py
```

종료: `q` 키

---

## 알고리즘 요약

### 졸음 감지 (`drowsiness.py`)
- **경로 A** (얼굴 보임): EAR이 캘리브레이션 임계값 이하로 ~1.8초 지속 → `DROWSINESS`
- **경로 B** (얼굴 안 보임): Pose pitch로 고개 숙임 3초 지속 → `DROWSINESS`

### 산만함 감지 (`fidget.py`)
- 코·어깨·팔꿈치 5개 키포인트의 프레임 간 이동량(motion energy) 측정
- 정상 대비 4배 이상 이동이 0.8초 지속 → burst 1회
- 30초 안에 burst 4회 이상 → `LOW_FOCUS`

### 하트 제스처 감지 (`heart.py`)
- 양손 MediaPipe Hands로 검지 끝 거리·굽힘 각도·엄지 방향 판별
- 7프레임 히스토리 과반수 충족 시 → `HEART`

---

## 새 Detector 추가 방법

1. `detectors/` 에 `BaseDetector` 상속 클래스 파일 생성
2. `process_frame(frame, now, rgb)`, `draw_hud(frame)`, `release()` 구현
3. `detectors/__init__.py` 에 import 및 `__all__` 에 추가
4. `signal_hub.py` 의 `DETECTORS` 리스트에 인스턴스 추가
5. `signal_hub.py` 의 `SIGNAL_STYLES` 에 시그널 이름·색상·라벨 등록

---

## 시그널 출력 연동

`signal_hub.py` 의 `on_signals()` 함수에서 `Signal` 객체를 수신

gui 에 signal 출력
