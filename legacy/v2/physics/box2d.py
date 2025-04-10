from Box2D import (
    b2World,
    b2Vec2,
    b2_dynamicBody,
    b2_staticBody,
    b2CircleShape,
    b2PolygonShape,
    b2ContactListener,
)
import numpy as np
from phyre2.physics.engine import PhysicsEngine
from phyre2.core.level import Level
from typing import Dict, Any


class GoalContactListener(b2ContactListener):
    def __init__(self, engine):
        super().__init__()
        self.engine = engine

    def BeginContact(self, contact):
        a = contact.fixtureA.body
        b = contact.fixtureB.body
        if hasattr(a, "userData") and hasattr(b, "userData"):
            if (
                self.engine.level
                and self.engine.level.goal
                and a.userData in self.engine.level.goal.objects
                and b.userData in self.engine.level.goal.objects
                and a.userData != b.userData
            ):
                self.engine._goal_achieved = True


class Box2DEngine(PhysicsEngine):
    def __init__(self, ppm: int = 60, fps: int = 60):
        self.ppm = ppm
        self.fps = fps
        self.world = b2World(gravity=(0, -10), doSleep=True)
        self.world.contactListener = GoalContactListener(self)
        self._bodies: Dict[str, Any] = {}
        self.level = None
        self.placed_action = False
        self._goal_achieved = False
        self.frameskip = 4
        self.time_step = 1.0 / self.fps
        self.vel_iters, self.pos_iters = 6, 2

    def load_level(self, level: Level):
        self.world.ClearForces()
        for body in self.world.bodies:
            self.world.DestroyBody(body)
        self.level = level
        self._bodies = {}
        self.placed_action = False
        self._goal_achieved = False

        for name, obj in level.objects.items():
            self._bodies[name] = self._create_body(obj)

        self._add_floor()

    def _create_body(self, obj):
        position = b2Vec2(*obj.position)
        body_type = b2_dynamicBody if obj.dynamic else b2_staticBody
        body = self.world.CreateBody(type=body_type, position=position, bullet=True)
        body.userData = obj.name

        if obj.type == "ball":
            radius = obj.size if isinstance(obj.size, float) else obj.size[0]
            shape = b2CircleShape(radius=radius)
            body.CreateFixture(shape=shape, density=1.0, friction=0.3, restitution=0.8)

        elif obj.type in ["platform", "basket"]:
            width, height = (
                obj.size if isinstance(obj.size, list) else [obj.size, obj.size]
            )
            shape = b2PolygonShape(box=(width / 2, height / 2))
            body.angle = np.radians(obj.angle)
            body.CreateFixture(shape=shape, density=1.0, friction=0.5)

        return body

    def _add_floor(self):
        floor_height = 0.2
        floor_shape = b2PolygonShape(box=(10, floor_height / 2))
        floor_body = self.world.CreateStaticBody(
            position=(0, -floor_height / 2), shapes=floor_shape
        )
        floor_body.userData = "__floor__"
        self._bodies["__floor__"] = floor_body

    def step(self, action: Any = None):
        if self.level is None:
            return

        if action is not None and not self.placed_action:
            action_objects = getattr(self.level, "action_objects", [])
            for i, obj_name in enumerate(action_objects):
                if obj_name in self._bodies:
                    target_pos = b2Vec2(float(action[i][0]), float(action[i][1]))
                    # y = max(y, 0.3)
                    self._bodies[obj_name].position = target_pos
            self.placed_action = True

        for _ in range(self.frameskip):  # substeps for smoother sim
            self.world.Step(self.time_step, self.vel_iters, self.pos_iters)

    def reset(self):
        self.world = b2World(gravity=(0, -10))
        self.world.contactListener = GoalContactListener(self)
        self._bodies = {}
        self.placed_action = False
        self._goal_achieved = False
        if self.level:
            self.load_level(self.level)

    def get_state(self):
        return {
            name: (body.position.x, body.position.y)
            for name, body in self._bodies.items()
            if name != "__floor__"
        }

    def is_goal_achieved(self) -> bool:
        return self._goal_achieved

    def is_stationary_world(self) -> bool:
        return all(body.linearVelocity == (0, 0) for body in self.world.bodies)

    def close(self):
        self.world.ClearForces()
        for body in self.world.bodies:
            self.world.DestroyBody(body)

    def objects(self) -> Dict[str, Any]:
        return self._bodies
