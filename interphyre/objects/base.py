from dataclasses import dataclass


@dataclass
class PhyreObject:
    """Base class for all physics objects in the world.

    This class defines the common properties that all physics objects share,
    including position, orientation, and physical properties like friction
    and restitution.

    Attributes:
        x (float): X-coordinate of the object's center position
        y (float): Y-coordinate of the object's center position
        angle (float): Rotation angle in degrees (default: 0.0)
        color (str): Visual color of the object (default: "black")
        dynamic (bool): Whether the object is affected by physics forces (default: True)
        restitution (float): Bounciness factor, 0.0 = no bounce, 1.0 = perfect bounce (default: 0.5)
        friction (float): Surface friction coefficient (default: 0.5)
        linear_damping (float): Linear velocity damping factor (default: 0.0)
        angular_damping (float): Angular velocity damping factor (default: 0.0)
        density (float): Density of the object (default: 1.0)
    """

    x: float
    y: float
    angle: float = 0.0  # in degrees
    color: str = "black"
    dynamic: bool = True
    restitution: float = 0.5
    friction: float = 0.5
    linear_damping: float = 0.0
    angular_damping: float = 0.0
    density: float = 1.0
