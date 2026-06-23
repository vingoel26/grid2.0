"""Stage 4 — the 8 violation analyzers (Part 4 of plan)."""
from .geometry import (
    crop,
    make_violation,
    object_overlaps_vehicle,
    point_in_polygon,
)
from .helmet import check_helmet
from .illegal_parking import check_illegal_parking
from .intersection import check_intersection
from .no_plate import check_no_plate
from .seatbelt import check_seatbelt
from .speeding import check_speeding
from .triple_riding import check_triple_riding
from .wrong_side import check_wrong_side

__all__ = [
    "crop",
    "make_violation",
    "object_overlaps_vehicle",
    "point_in_polygon",
    "check_helmet",
    "check_illegal_parking",
    "check_intersection",
    "check_no_plate",
    "check_seatbelt",
    "check_speeding",
    "check_triple_riding",
    "check_wrong_side",
]
