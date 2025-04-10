from dataclasses import dataclass, field
from typing import Dict, Callable, List, Optional
from phyre2.objects import PhyreObject


@dataclass
class Level:
    name: str
    objects: Dict[str, PhyreObject]
    action_objects: List[str]
    success_condition: Callable  # function(engine) -> bool
    target_object: Optional[str] = None
    goal_object: Optional[str] = None
    metadata: Optional[dict] = field(default_factory=dict)

    def __post_init__(self):
        if not callable(self.success_condition):
            raise ValueError(
                f"Level '{self.name}' must define a success_condition function."
            )

    def move_object(self, obj_name: str, x: float, y: float):
        if obj_name in self.objects:
            self.objects[obj_name].x, self.objects[obj_name].y = x, y
        else:
            raise ValueError(f"No object named '{obj_name}' in level.")

    def set_angle(self, obj_name: str, angle: float):
        if obj_name in self.objects:
            self.objects[obj_name].angle = angle
        else:
            raise ValueError(f"No object named '{obj_name}' in level.")

    def change_color(self, obj_name: str, color: str):
        if obj_name in self.objects:
            self.objects[obj_name].color = color
        else:
            raise ValueError(f"No object named '{obj_name}' in level.")

    def remove_object(self, obj_name: str):
        if obj_name in self.objects:
            del self.objects[obj_name]
            if obj_name in self.action_objects:
                self.action_objects.remove(obj_name)
            if self.target_object == obj_name:
                self.target_object = None
            if self.goal_object == obj_name:
                self.goal_object = None
        else:
            raise ValueError(f"Cannot remove: No object named '{obj_name}' in level.")

    def set_dynamic(self, obj_name: str, dynamic: bool):
        if obj_name in self.objects:
            self.objects[obj_name].dynamic = dynamic
        else:
            raise ValueError(f"No object named '{obj_name}' in level.")

    def set_restitution(self, obj_name: str, restitution: float):
        if obj_name in self.objects:
            self.objects[obj_name].restitution = restitution
        else:
            raise ValueError(f"No object named '{obj_name}' in level.")

    def set_friction(self, obj_name: str, friction: float):
        if obj_name in self.objects:
            self.objects[obj_name].friction = friction
        else:
            raise ValueError(f"No object named '{obj_name}' in level.")

    def clone(self, new_name: Optional[str] = None):
        import copy

        return Level(
            name=new_name or self.name + "_clone",
            objects=copy.deepcopy(self.objects),
            action_objects=self.action_objects[:],
            target_object=self.target_object,
            goal_object=self.goal_object,
            success_condition=self.success_condition,
            metadata=copy.deepcopy(self.metadata),
        )
