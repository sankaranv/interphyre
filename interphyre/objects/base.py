from dataclasses import dataclass


@dataclass
class PhyreObject:
    x: float
    y: float
    angle: float = 0.0  # in degrees
    color: str = "black"
    dynamic: bool = True
    restitution: float = 0.5
    friction: float = 0.5


