from phyre2.box2d_objects import *
import os
from phyre2.utils import *
import gymnasium as gym
from Box2D import b2World, b2Vec2
import numpy as np
import pygame
from phyre2.rendering import render_scene
import json


class PHYRELevel:
    def __init__(self, level=None):
        self.objects = {}
        self.bodies = {}
        self.target_object = None
        self.goal_object = None
        self.action_objects = []
        self.name = "EmptyLevel"
        self.solution = None

        if level is not None:
            if isinstance(level, PHYRELevel):
                self.load(level)
            elif isinstance(level, str):
                self.load_from_file(level)
            elif isinstance(level, dict):
                self.load_dict(level)
            else:
                raise Exception(f"Level {level} is not a valid type")

    def load_from_file(self, level_name, with_solution=True, level_dir="levels/"):
        """
        Load a level from a JSON file and create the appropriate Box2D bodies
        :param level_name:
        :param level_dir:
        :return:
        """

        with open(f"{level_dir}/{level_name}.json", "r") as f:
            level = json.load(f)
        self.load_dict(level, with_solution)

    def load(self, level, with_solution=True):
        """
        Load a level from a PHYRELevel object and create the appropriate Box2D bodies
        :param level:
        :return:
        """

        self.objects = level.objects
        self.target_object = level.target_object
        self.action_objects = level.action_objects
        self.goal_object = level.goal_object
        self.name = level.name
        self.solution = level.solution

    def load_dict(self, level_dict, with_solution=True):
        """
        Load a level from dictionary and create the appropriate Box2D bodies
        :param level:
        :return:
        """

        self.objects = {}
        for name, obj in level_dict["objects"].items():
            if obj["type"] == "basket":
                self.objects[name] = Basket(
                    obj["x"], obj["y"], obj["scale"], obj["color"], obj["dynamic"]
                )
            elif obj["type"] == "ball":
                self.objects[name] = Ball(
                    obj["x"], obj["y"], obj["radius"], obj["color"], obj["dynamic"]
                )
            elif obj["type"] == "platform":
                self.objects[name] = Platform(
                    obj["x"],
                    obj["y"],
                    obj["length"],
                    obj["angle"],
                    obj["color"],
                    obj["dynamic"],
                )
            else:
                raise Exception(f"Object {obj} is not a valid type")
        self.target_object = level_dict["target_object"]
        self.action_objects = level_dict["action_objects"]
        self.goal_object = level_dict["goal_object"]
        self.name = level_dict["name"]
        if with_solution:
            self.solution = level_dict["solution"]
        else:
            self.solution = None

    def save(self, level_name, level_dir="levels"):
        """
        Save the current level to a JSON file
        :param level_name:
        :param level_dir:
        :return:
        """
        level = {
            "name": level_name,
            "objects": {},
            "target_object": self.target_object,
            "action_objects": self.action_objects,
        }
        for name, obj in self.objects.items():
            if isinstance(obj, Basket):
                level["objects"][name] = {
                    "x": obj.x,
                    "y": obj.y,
                    "scale": obj.scale,
                    "color": obj.color,
                    "dynamic": obj.dynamic,
                    "type": "basket",
                }
            elif isinstance(obj, Ball):
                level["objects"][name] = {
                    "x": obj.x,
                    "y": obj.y,
                    "radius": obj.radius,
                    "color": obj.color,
                    "dynamic": obj.dynamic,
                    "type": "ball",
                }
            elif isinstance(obj, Platform):
                level["objects"][name] = {
                    "x": obj.x,
                    "y": obj.y,
                    "length": obj.length,
                    "angle": obj.angle,
                    "color": obj.color,
                    "dynamic": obj.dynamic,
                    "type": "platform",
                }
            else:
                raise Exception(f"Object {obj} is not a valid type")
        if not os.path.exists(level_dir):
            os.makedirs(level_dir)
        with open(f"{level_dir}/{level_name}.json", "w") as f:
            json.dump(level, f, indent=4)

    def is_valid_level(self):
        # TODO: Check for overlapping objects
        if not self.objects:
            print("No objects found in level")
            return False
        elif not self.target_object:
            print("No target found in level")
            return False
        elif not self.action_objects:
            print("No action object found in level")
            return False
        elif not self.goal_object:
            print("No goal object found in level")
            return False
        elif self.target_object not in self.objects:
            print(f"Target object {self.target_object} not found in level")
            return False
        elif self.goal_object not in self.objects:
            print(f"Goal object {self.goal_object} not found in level")
            return False
        else:
            for action_object in self.action_objects:
                if action_object not in self.objects:
                    print(f"Action {action_object} not found in level")
                    return False

        return True

    def make_level(self, world, screen_width, screen_height, ppm):
        self.bodies = {}
        # Create walls on the edges of the screen
        left_wall, right_wall, top_wall, bottom_wall = create_walls(
            world, 0.01, screen_width / ppm, screen_height / ppm
        )
        self.bodies["left_wall"] = left_wall
        self.bodies["right_wall"] = right_wall
        self.bodies["top_wall"] = top_wall
        self.bodies["bottom_wall"] = bottom_wall

        # Make sure action objects and target objects are dynamic
        for name in self.action_objects:
            self.objects[name].dynamic = True
        self.objects[self.target_object].dynamic = True

        # Check for each dataclass type and create the appropriate Box2D body
        for name, obj in self.objects.items():
            if isinstance(obj, Basket):
                self.bodies[name] = create_basket(world, obj, name)
            elif isinstance(obj, Ball):
                self.bodies[name] = create_ball(world, obj, name)
            elif isinstance(obj, Platform):
                self.bodies[name] = create_platform(world, obj, name)
            else:
                raise Exception(f"Object {obj} is not a valid type")

    def null_object(self, world, obj_name):
        """
        Null out the object with the given name
        :param world:
        :param obj_name:
        """
        # Make sure the object exists
        if obj_name not in self.objects:
            raise Exception(f"Object {obj_name} not found in level")
        # Make sure not to null the basket or target
        if obj_name == "basket":
            raise Exception(f"Cannot null the basket")
        elif obj_name == self.target:
            raise Exception(f"Cannot null the target object")
        elif obj_name in self.action_objects:
            raise Exception(f"Cannot null an action object")
        else:
            # Remove the object from the world
            for body in world.bodies:
                if body.userData == obj_name:
                    world.DestroyBody(body)
            # Remove the object from the level
            del self.objects[obj_name]

    def add_object(self, world, obj, name, is_action_object=False):
        """
        Add an object to the level
        :param world:
        :param obj:
        :param name:
        :param is_action_object:
        :return:
        """

        # Make sure the object doesn't already exist
        if obj.name in self.objects:
            raise Exception(f"Object {obj.name} already exists in level")
        # Make sure the object is not the basket or target
        if obj.name == "basket":
            raise Exception(f"Cannot add the basket")
        elif obj.name == self.target:
            raise Exception(f"Cannot add the target object")
        else:
            # Add the object to the world
            if isinstance(obj, Basket):
                create_basket(world, obj, name)
            elif isinstance(obj, Ball):
                create_ball(world, obj, name)
            elif isinstance(obj, Platform):
                create_platform(world, obj, name)
            else:
                raise Exception(f"Object {obj} is not a valid type")
            # Add the object to the level
            self.objects[name] = obj
            if is_action_object:
                self.action_objects.append(name)


class PHYREWorld(gym.Env):
    def __init__(
        self,
        level,
        screen_size=600,
        ppm=60,
        max_steps=1000,
        fps=60,
        vel_iters=6,
        pos_iters=2,
        render_level=True,
    ):
        super().__init__()

        # Set up world
        self.level = level
        self.world = b2World(gravity=(0, -10), doSleep=True)
        self.screen_size = screen_size
        self.max_steps = max_steps
        self.fps = fps
        self.ppm = ppm
        self.vel_iters = vel_iters
        self.pos_iters = pos_iters
        self.render_level = render_level
        self.success = False
        self.done = False
        self.info = {}

        if self.render_level:
            # Pygame setup
            pygame.init()
            self.screen = pygame.display.set_mode((screen_size, screen_size))
            pygame.display.set_caption(f"PHYRE2: {self.level.name}")

        # Set up observation space
        self.observation_space = gym.spaces.Box(
            low=np.array(
                [-screen_size / self.ppm * 0.5, -screen_size / self.ppm * 0.5]
            ),
            high=np.array([screen_size / self.ppm * 0.5, screen_size / self.ppm * 0.5]),
            dtype=np.float32,
        )

        # The number of action_objects to take is specified in the level
        num_action_objects = len(self.level.action_objects)
        action_space_low = np.tile(
            np.array([-screen_size / self.ppm * 0.5, -screen_size / self.ppm * 0.5]),
            (num_action_objects, 1),
        )
        action_space_high = np.tile(
            np.array([screen_size / self.ppm * 0.5, screen_size / self.ppm * 0.5]),
            (num_action_objects, 1),
        )

        # If there is only one action_object, then the action_object space should be just 2D
        if num_action_objects == 1:
            action_space_low = action_space_low.flatten()
            action_space_high = action_space_high.flatten()

        self.action_space = gym.spaces.Box(
            low=action_space_low,
            high=action_space_high,
            dtype=np.float32,
        )

        # Set up collision handler
        self.world.contactListener = GoalContactListener(self)

        self.reset()

    def reset(self):
        # Reset the world
        self.world.ClearForces()
        for body in self.world.bodies:
            self.world.DestroyBody(body)

        # Reset the level
        self.level.make_level(self.world, self.screen_size, self.screen_size, self.ppm)

    def _get_observation(self):
        # TODO - add state information for all objects including collision detections
        return self.level.bodies[self.level.target_object].position

    def _calculate_reward(self, success):
        # TODO - add reward function
        return 1.0 if success else 0.0

    def step(self, action):
        info = {}
        # Set positions for all action_object objects
        if len(self.level.action_objects) == 1:
            action = [action]
        for i, obj_name in enumerate(self.level.action_objects):
            target_position = action[i]
            target_position = b2Vec2(
                float(target_position[0]), float(target_position[1])
            )
            self.level.bodies[obj_name].position = target_position

        # Run the simulation for a fixed number of steps
        clock = pygame.time.Clock()
        num_steps = 0
        self.success = False
        self.done = False
        while not self.done and num_steps < self.max_steps:
            # Close the window if the user clicks the close button
            if self.render_level:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.done = True

            # Step Box2D simulation
            time_step = 1.0 / self.fps
            self.world.Step(time_step, self.vel_iters, self.pos_iters)
            num_steps += 1

            # Check if the world is stationary
            if detect_stationary_world(self.world, self.level):
                self.info["termination"] = "STATIONARY_WORLD"
                self.success = False
                self.done = True

            # Clear the screen and render the world
            if self.render_level:
                self.render(mode="human")
                clock.tick(60)

        if num_steps >= self.max_steps:
            self.info["termination"] = "TIMEOUT"

        # Calculate reward
        reward = self._calculate_reward(self.success)

        # Return the observation, reward, done, and info
        obs = self._get_observation()
        return obs, reward, self.done, self.info

    def render(self, mode="human"):
        self.screen.fill((255, 255, 255))
        render_scene(self.world, self.level, self.screen, self.ppm)
        pygame.display.flip()

    def close(self):
        # Reset the world
        self.world.ClearForces()
        for body in self.world.bodies:
            self.world.DestroyBody(body)

        # Quit pygame
        if self.render_level:
            pygame.quit()
