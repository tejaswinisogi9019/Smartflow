"""
=====================================================================
 SmartFlow AI - Camera Stream Handler (Phase 4 with YOLO)
---------------------------------------------------------------------
"""

import cv2
import numpy as np
from detection import detector

class VideoCamera:
    def __init__(self):
        self.video = None
        self.is_running = False
        self.source = None

    def start(self, source=0):
        if self.video is not None:
            self.stop()

        self.source = source
        if isinstance(source, str) and source.isdigit():
            self.source = int(source)

        self.video = cv2.VideoCapture(self.source)

        if not self.video.isOpened():
            print(f"[Camera Error] Could not open video source: {self.source}")
            self.video = None
            self.is_running = False
            return False

        self.is_running = True
        print(f"[Camera] Connected successfully to source: {self.source}")
        return True

    def stop(self):
        self.is_running = False
        if self.video is not None:
            self.video.release()
            self.video = None
        print("[Camera] Stopped.")

    def get_frame(self):
        if not self.is_running or self.video is None:
            return self.get_placeholder_frame("CAMERA OFFLINE")

        success, frame = self.video.read()

        if not success:
            # If a video file ends, loop back to the start
            if isinstance(self.source, str):
                self.video.set(cv2.CAP_PROP_POS_FRAMES, 0)
                success, frame = self.video.read()

            if not success:
                return self.get_placeholder_frame("FEED INTERRUPTED")

        # Resize for smooth AI inference and web streaming
        frame = cv2.resize(frame, (640, 480))

        # PASS FRAME THROUGH YOLO DETECTION AND TRACKING
        processed_frame, _ = detector.process_frame(frame)

        # Convert to JPEG bytes
        ret, jpeg = cv2.imencode('.jpg', processed_frame)
        if not ret:
            return None
        return jpeg.tobytes()

    def get_placeholder_frame(self, message="NO FEED"):
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(frame, message, (180, 240),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (148, 163, 184), 2)
        cv2.putText(frame, "SmartFlow AI Monitoring", (200, 280),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (56, 189, 248), 1)

        ret, jpeg = cv2.imencode('.jpg', frame)
        return jpeg.tobytes()


global_camera = VideoCamera()