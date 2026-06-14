import cv2
import mediapipe as mp
import threading


class GestureInput:
    def __init__(self):
        self._gesture = None
        self._lock = threading.Lock()
        self._running = False
        self._thread = None

        self._mp_hands = mp.solutions.hands
        self._hands = self._mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.6,
        )

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._running = True
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

    def get_current_gesture(self) -> str | None:
        with self._lock:
            return self._gesture

    def consume_gesture(self) -> str | None:
        with self._lock:
            g = self._gesture
            self._gesture = None
            return g

    def _capture_loop(self):
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("[GestureInput] 無法開啟攝影機")
            return

        while self._running:
            ret, frame = cap.read()
            if not ret:
                continue

            frame  = cv2.flip(frame, 1)
            rgb    = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = self._hands.process(rgb)

            gesture = None
            if result.multi_hand_landmarks:
                landmarks = result.multi_hand_landmarks[0].landmark
                gesture   = self._classify(landmarks)

            with self._lock:
                self._gesture = gesture

            self._draw_debug(frame, result, gesture)
            cv2.imshow("Gesture Cam", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                self._running = False

        cap.release()
        cv2.destroyAllWindows()

    def _classify(self, landmarks) -> str | None:

        def finger_up(tip: int, pip: int) -> bool:
            """指尖 Y 座標小於 PIP 關節 → 手指伸直"""
            return landmarks[tip].y < landmarks[pip].y

        index_up  = finger_up(8,  6)
        middle_up = finger_up(12, 10)
        ring_up   = finger_up(16, 14)
        pinky_up  = finger_up(20, 18)
        thumb_up  = landmarks[4].x < landmarks[3].x  # 鏡像後：tip 在 IP 左側為伸出

        # ── ✌️ 剪刀（最優先，避免被 fist 攔截）──
        # 食指＋中指伸直，無名指＋小指彎曲，大拇指不限
        if index_up and middle_up and not ring_up and not pinky_up:
            return "scissors"

        # ── 👍 比讚 ──
        # 大拇指伸出，食指/中指/無名指/小指全彎
        if thumb_up and not index_up and not middle_up and not ring_up and not pinky_up:
            return "thumbs_up"

        # ── ✋ 手掌 ──
        # 食指/中指/無名指/小指全部伸直
        if index_up and middle_up and ring_up and pinky_up:
            return "open_palm"

        # ── ✊ 握拳（待機）──
        # 四指全彎 → 回傳 None，不觸發任何判定
        if not index_up and not middle_up and not ring_up and not pinky_up:
            return None

        # 其他過渡姿勢
        return None

    def _draw_debug(self, frame, result, gesture: str | None):
        mp_draw = mp.solutions.drawing_utils
        if result.multi_hand_landmarks:
            for hand_lm in result.multi_hand_landmarks:
                mp_draw.draw_landmarks(
                    frame, hand_lm, self._mp_hands.HAND_CONNECTIONS
                )
        label = gesture if gesture else "[ standby - fist ]"
        color = (0, 255, 0) if gesture else (100, 100, 100)
        cv2.putText(frame, label, (10, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 2)