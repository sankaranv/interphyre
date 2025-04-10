from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, field


@dataclass
class Object:
    name: str
    type: str  # e.g., 'ball', 'bar', 'basket', etc.
    position: List[float]  # [x, y] center or bottom-left, depending on type
    size: Union[float, List[float]]  # radius or [width, height]
    angle: float = 0.0
    color: Optional[str] = None
    dynamic: bool = True
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Goal:
    type: str  # e.g., 'touching', 'above', etc.
    objects: List[str]  # e.g., ["ball", "basket"]


@dataclass
class Level:
    name: str = "UnnamedLevel"
    description: Optional[str] = None
    objects: Dict[str, Object] = field(default_factory=dict)
    goal: Optional[Goal] = None
    action_objects: List[str] = field(default_factory=list)
    solution_tier: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_object(self, name: str, obj: Object):
        self.objects[name] = obj

    def remove_object(self, name: str):
        if name in self.objects:
            del self.objects[name]

    def get_object(self, name: str) -> Optional[Object]:
        return self.objects.get(name)

    def set_goal(self, goal_type: str, objects: List[str]):
        self.goal = Goal(type=goal_type, objects=objects)

    def all_objects(self) -> List[Object]:
        return list(self.objects.values())
