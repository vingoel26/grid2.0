"""Model wrappers. Each lazily loads weights and degrades gracefully when a
model file is missing, so the pipeline runs end-to-end before real weights land.
"""
from .vehicle_detector import VehicleDetector
from .person_detector import PersonDetector
from .plate_detector import PlateDetector
from .seatbelt_detector import SeatbeltDetector
from .helmet_classifier import HelmetClassifier
from .scene_classifier import SceneClassifier
from .plate_ocr import PlateOCR

__all__ = [
    "VehicleDetector",
    "PersonDetector",
    "PlateDetector",
    "SeatbeltDetector",
    "HelmetClassifier",
    "SceneClassifier",
    "PlateOCR",
]
