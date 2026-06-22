"""Service to resolve license plate numbers to owner details."""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path

log = logging.getLogger("backend.owner_lookup")


@dataclass
class OwnerInfo:
    name: str
    phone: str
    email: str
    address: str


class MockOwnerRegistry:
    """Mock registry reading from configs/owner_registry.json."""
    
    def __init__(self, config_path: str | Path):
        self.config_path = Path(config_path)
        self._registry: dict[str, dict] = {}
        self._load()

    def _load(self):
        if not self.config_path.exists():
            log.warning(f"Owner registry config not found at {self.config_path}")
            return
        try:
            with open(self.config_path, "r") as f:
                self._registry = json.load(f)
            log.info(f"Loaded {len(self._registry)} owner records from {self.config_path}")
        except Exception as e:
            log.error(f"Failed to load owner registry from {self.config_path}: {e}")

    def lookup(self, plate: str) -> OwnerInfo | None:
        if not plate:
            return None
            
        # Normalize plate (remove spaces, upper case)
        plate_norm = "".join(plate.split()).upper()
        
        info = self._registry.get(plate_norm)
        if not info:
            # For testing: if plate not found, return a dummy owner
            # so we can still test the pipeline
            log.info(f"Plate {plate_norm} not found in registry, returning dummy owner")
            return OwnerInfo(
                name="Unknown Owner",
                phone="+910000000000",
                email="unknown@example.com",
                address="Address Unknown"
            )
            
        return OwnerInfo(
            name=info.get("name", "Unknown"),
            phone=info.get("phone", ""),
            email=info.get("email", ""),
            address=info.get("address", "")
        )


# Singleton instance
# The path is relative to where main.py sets up the environment
import os
from ..main import CONFIG_DIR
registry = MockOwnerRegistry(CONFIG_DIR / "owner_registry.json")


def lookup_owner(plate: str) -> OwnerInfo | None:
    """
    Main entry point for owner lookup.
    Currently uses MockOwnerRegistry. 
    Can be updated to use a real Vahan/RTO API.
    """
    return registry.lookup(plate)
