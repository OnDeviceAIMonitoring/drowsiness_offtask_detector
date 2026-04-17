"""
Signal Hub — 여러 감지기(Detector)를 통합 실행하는 오케스트레이터
▸ 카메라 1개로 프레임을 캡처
▸ 등록된 모든 Detector에 프레임 전달
▸ 각 Detector가 반환한 Signal을 수집·표시·전달

"""
import cv2
import time

from detectors import DrowsinessDetector, FidgetDetector, OffTaskDetector, HeartDetector, Signal, SharedMediaPipe

# ─────────────────────────────────────────────────────────────
#  감지기 등록 — 새 Detector를 여기에 추가하면 자동으로 동작합니다
# ─────────────────────────────────────────────────────────────
DETECTORS = [
    DrowsinessDetector(),
    FidgetDetector(),
    HeartDetector(),
    OffTaskDetector(),
]

shared_mp = SharedMediaPipe()

# ─────────────────────────────────────────────────────────────
#  시그널 콜백 — 수신된 시그널을 처리하는 함수
# ─────────────────────────────────────────────────────────────
def on_signals(signals: list[Signal]) -> None:
    """
    매 프레임에서 수집된 시그널 목록을 받아 처리합니다.
    여기에 원하는 출력을 추가하세요:
      - GPIO (부저, LED)
      - MQTT / WebSocket 전송
      - 로그 파일 기록
      - 등등
    """
    for sig in signals:
        print(sig)


# ─────────────────────────────────────────────────────────────
#  HUD: 통합 알림 바
# ─────────────────────────────────────────────────────────────
# 시그널 종류별 색상 / 라벨 매핑
SIGNAL_STYLES = {
    "DROWSINESS": {"color": (0, 0, 200),    "label": "DROWSINESS"},  # 빨강
    "LOW_FOCUS":  {"color": (0, 100, 220),  "label": "LOW_FOCUS"},   # 주황
    "HEART":      {"color": (180, 0, 180),  "label": "BIG HEART!"},  # 보라
    "OFF_TASK":   {"color": (252, 180, 14),  "label": "OFF_TASK"},    # 파랑
}
_DEFAULT_STYLE = {"color": (180, 180, 0), "label": "alarm"}            # 미등록 시그널 기본


def draw_alert_bar(frame, signals: list[Signal]) -> None:
    """시그널이 있으면 화면 하단에 시그널 종류별 알림 바 표시"""
    if not signals:
        return
    h, w = frame.shape[:2]

    # 중복 제거 — 시그널 종류(name) 기준
    seen_names = sorted(set(s.name for s in signals))

    # 가장 위험한 종류의 색상을 바 배경으로 사용
    priority = list(SIGNAL_STYLES.keys())
    bar_color = _DEFAULT_STYLE["color"]
    for name in priority:
        if name in seen_names:
            bar_color = SIGNAL_STYLES[name]["color"]
            break

    # 라벨 조합
    labels = []
    for name in seen_names:
        style = SIGNAL_STYLES.get(name, _DEFAULT_STYLE)
        labels.append(style["label"])
    text = " & ".join(labels)

    cv2.rectangle(frame, (0, h - 40), (w, h), bar_color, -1)
    cv2.putText(frame, text, (10, h - 12),
                cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)


# ─────────────────────────────────────────────────────────────
#  메인 루프
# ─────────────────────────────────────────────────────────────
def main():
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    prev_time = time.time()

    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            now = time.time()
            fps = 1.0 / max(now - prev_time, 1e-6)
            prev_time = now

            # ── BGR→RGB 변환 1회 (모든 감지기 공유) ──────────
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            shared_mp.process(rgb)

            # ── 모든 감지기 실행 ──────────────────────────────
            all_signals: list[Signal] = []
            for det in DETECTORS:
                sigs = det.process_frame(frame, now, shared_mp)
                all_signals.extend(sigs)

            # ── 시그널 콜백 ───────────────────────────────────
            if all_signals:
                on_signals(all_signals)

            # ── HUD 그리기 ────────────────────────────────────
            for det in DETECTORS:
                det.draw_hud(frame)
            draw_alert_bar(frame, all_signals)

            # FPS
            h, w = frame.shape[:2]
            cv2.putText(frame, f"FPS:{fps:.1f}", (w - 120, 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (180, 180, 180), 1)

            cv2.imshow("Signal Hub", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()
        shared_mp.release()
        for det in DETECTORS:
            det.release()


if __name__ == "__main__":
    main()
