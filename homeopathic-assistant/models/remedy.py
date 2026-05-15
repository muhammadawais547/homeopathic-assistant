# models/remedy.py
from dataclasses import dataclass
from typing import Optional


@dataclass
class Remedy:
    id: int
    abbreviation: str
    name: Optional[str] = None
    thermal_type: Optional[str] = None