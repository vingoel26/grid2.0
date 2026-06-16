"""Stage 4 — the 8 violation analyzers (Part 4 of plan)."""
from .helmet import check_helmet
from .seatbelt import check_seatbelt
from .triple_riding import check_triple_riding
from .wrong_side import check_wrong_side
from .intersection import check_intersection
from .illegal_parking import check_illegal_parking
from .no_plate import check_no_plate

__all__ = [
    "check_helmet",
    "check_seatbelt",
    "check_triple_riding",
    "check_wrong_side",
    "check_intersection",
    "check_illegal_parking",
    "check_no_plate",
]
