"""
=====================================================================
 SmartFlow AI - Directional 4-Quadrant Vehicle Detection
=====================================================================
"""

import cv2
import numpy as np

class VehicleTracker:
    def __init__(self):
        # Motion background extractor
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=300, varThreshold=50, detectShadows=False
        )
        self.tracked_objects = {}
        self.next_object_id = 1
        
        self.directional_counts = {
            "North": 0,
            "South": 0,
            "East": 0,
            "West": 0
        }
        self.total_count = 0

    def process_frame(self, frame):
        if frame is None:
            return None, self.directional_counts

        height, width, _ = frame.shape
        mid_x, mid_y = width // 2, height // 2

        # 1. Preprocessing for vehicle motion detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        fg_mask = self.bg_subtractor.apply(blur)
        
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        dilated = cv2.dilate(fg_mask, kernel, iterations=2)
        closing = cv2.morphologyEx(dilated, cv2.MORPH_CLOSE, kernel)

        contours, _ = cv2.findContours(closing, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        current_detections = []
        dir_counts = {"North": 0, "South": 0, "East": 0, "West": 0}

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < 1200:
                continue

            x, y, w, h = cv2.boundingRect(cnt)
            cx, cy = x + w // 2, y + h // 2

            # Determine Quadrant direction based on Centroid
            if cy < mid_y and cx < mid_x:
                direction = "North"
            elif cy >= mid_y and cx < mid_x:
                direction = "West"
            elif cy < mid_y and cx >= mid_x:
                direction = "East"
            else:
                direction = "South"

            aspect_ratio = float(w) / max(h, 1)
            if area > 18000:
                class_name = "Bus" if aspect_ratio > 1.2 else "Truck"
            elif area > 5000:
                class_name = "Car"
            elif aspect_ratio < 0.85:
                class_name = "Motorcycle"
            else:
                class_name = "Car"

            current_detections.append((x, y, w, h, cx, cy, class_name, direction))

        # 2. Centroid Tracking to prevent duplicate counts
        new_tracked_objects = {}
        for (x, y, w, h, cx, cy, class_name, direction) in current_detections:
            matched_id = None
            min_dist = 60

            for obj_id, (ox, oy, oclass, odir, _) in self.tracked_objects.items():
                dist = np.hypot(cx - ox, cy - oy)
                if dist < min_dist:
                    min_dist = dist
                    matched_id = obj_id

            if matched_id is None:
                matched_id = self.next_object_id
                self.next_object_id += 1

            new_tracked_objects[matched_id] = (cx, cy, class_name, direction, 0)
            dir_counts[direction] += 1

            # Draw vehicle bounding boxes
            cv2.rectangle(frame, (x, y), (x + w, y + h), (248, 189, 56), 2)
            cv2.circle(frame, (cx, cy), 4, (0, 255, 255), -1)

            label = f"#{matched_id} {class_name} [{direction}]"
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
            cv2.rectangle(frame, (x, y - 18), (x + tw + 6, y), (248, 189, 56), -1)
            cv2.putText(frame, label, (x + 3, y - 4),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.42, (15, 23, 42), 1, cv2.LINE_AA)

        self.tracked_objects = new_tracked_objects
        self.directional_counts = dir_counts
        self.total_count = sum(dir_counts.values())

        # 3. Draw 4-Quadrant Division Grid on Video
        cv2.line(frame, (mid_x, 0), (mid_x, height), (56, 189, 248), 1, cv2.LINE_AA)
        cv2.line(frame, (0, mid_y), (width, mid_y), (56, 189, 248), 1, cv2.LINE_AA)

        # Quadrant HUD Labels
        cv2.putText(frame, f"NORTH: {dir_counts['North']}", (20, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (34, 197, 94), 2)
        cv2.putText(frame, f"EAST: {dir_counts['East']}", (mid_x + 20, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (34, 197, 94), 2)
        cv2.putText(frame, f"WEST: {dir_counts['West']}", (20, mid_y + 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (34, 197, 94), 2)
        cv2.putText(frame, f"SOUTH: {dir_counts['South']}", (mid_x + 20, mid_y + 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (34, 197, 94), 2)

        return frame, self.directional_counts

    def get_directional_counts(self):
        return self.directional_counts

    def get_counts(self):
        return self.directional_counts


# ==========================================================
# THIS LINE CREATES THE DETECTOR OBJECT (MUST BE PRESENT)
# ==========================================================
detector = VehicleTracker()