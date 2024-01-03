import json
import os
from phyre2.environment import PHYREWorld, PHYRELevel
from phyre2.objects import Ball, Basket, Platform
from phyre2.rendering import system_colors
import yaml


class PHYRETemplate:
    def __init__(self):
        """
        Initializes the template
        Args:
            template_name:
            template_path:

        Returns:

        """
        self.name = "empty_task"
        self.description = "This is the base class for tasks, do not use this as-is!"
        self.objects = {}
        self.target_object = None
        self.goal_object = None
        self.action_objects = []
        self.build_task()

    def build_task(self):
        """
        Randomly builds a level for the given task
        This function should be reimplemented for each task

        Returns: task

        """
        raise NotImplementedError

    def create_level(self, level_name, check_solvable=True, max_trials=100):
        """
        Creates a level from the template
        Args:
            level_name:
            check_solvable:
            max_trials:

        Returns:

        """
        # Check if the template is valid
        assert self.is_valid_task()

        # Generate level attributes from the template
        self.build_task()

        # Create the level
        level = {
            "name": level_name,
            "objects": {},
            "target_object": self.target_object,
            "goal_object": self.goal_object,
            "action_objects": self.action_objects,
        }

        for name, task_obj in self.objects.items():
            # Create object
            level_obj = {}

            # Get object type
            if isinstance(task_obj, Ball):
                level_obj["type"] = "ball"
                level_obj["radius"] = task_obj.radius
            elif isinstance(task_obj, Basket):
                level_obj["type"] = "basket"
                level_obj["scale"] = task_obj.scale
                level_obj["angle"] = task_obj.angle
            elif isinstance(task_obj, Platform):
                level_obj["type"] = "platform"
                level_obj["length"] = task_obj.length
                level_obj["angle"] = task_obj.angle
            else:
                raise ValueError(f"Object {name} is not a valid object type")

            # Set the remaining attributes
            level_obj["x"] = task_obj.x
            level_obj["y"] = task_obj.y
            level_obj["color"] = task_obj.color
            level_obj["dynamic"] = task_obj.dynamic

            # Add object to level
            level["objects"][name] = level_obj

        # Test if the level can be solved
        if check_solvable:
            solution = self.solve_level(level, max_trials=max_trials)
            if solution is None:
                return None
            else:
                level["solution"] = solution.tolist()
                return level

        level["solution"] = None
        return level

    def solve_level(self, level_dict, max_trials=100, env_config_path="./"):
        # Load the simulator config from YAML
        env_config = yaml.load(
            open(os.path.join(env_config_path, "config.yaml"), "r"),
            Loader=yaml.FullLoader,
        )
        level = PHYRELevel()
        level.load_dict(level_dict, with_solution=False)
        env = PHYREWorld(
            level,
            fps=env_config["fps"],
            screen_size=env_config["screen_size"],
            vel_iters=env_config["vel_iters"],
            pos_iters=env_config["pos_iters"],
            max_steps=env_config["max_steps"],
            render_level=False,
        )

        # Take random actions until a usable solution is found
        # TODO - using a policy that is actually good would probably be better
        for i in range(max_trials):
            action = env.action_space.sample()
            observation, reward, done, info = env.step(action)
            termination = info["termination"]
            env.reset()
            if termination == "SUCCESS":
                solution = action
                return solution
        return None

    def generate_random_levels(
        self,
        num_levels,
        check_solvable=False,
        save_to_file=False,
        max_trials=None,
        level_path="levels/",
    ):
        """
        Generates levels from the template
        Args:
            template:
            num_levels:
            check_solvable:
            save_to_file:
            max_trials:
            level_path:

        Returns:

        """
        if max_trials is None:
            max_trials = 100 * num_levels

        # Generate levels
        levels = []
        idx = 0
        total_trials = 0
        while idx < num_levels and total_trials < max_trials:
            level_name = f"{self.name}_{idx+1}"
            level = self.create_level(level_name, check_solvable)
            total_trials += 1
            if level:
                levels.append(level)
                idx += 1
        if save_to_file:
            for level in levels:
                self.write_level_to_file(level, level_path)
        print(len(levels))
        return levels

    def write_level_to_file(self, level, level_path):
        """
        Writes the level to file
        Args:
            level:
            template_name:
            level_path:

        Returns: None

        """
        if not os.path.exists(os.path.join(level_path, self.name)):
            os.makedirs(os.path.join(level_path, self.name))
        json.dump(
            level,
            open(os.path.join(level_path, self.name, f"{level['name']}.json"), "w"),
            indent=4,
        )

    def is_valid_task(self):
        """
        Checks if the level is valid
          Args:
              level:
        Returns: True if the level is valid, False otherwise
        """

        # Check if the level is a dictionary
        if (
            self.objects is None
            or not isinstance(self.objects, dict)
            or len(self.objects) == 0
        ):
            print(f"Objects are missing or not stored as a dictionary")
            return False

        # Check if the level has target objects
        if (
            self.target_object is None
            or not isinstance(self.target_object, str)
            or self.target_object not in self.objects
        ):
            print(f"Level does not have target object")
            return False

        # Check if the level has goal objects
        if (
            self.goal_object is None
            or not isinstance(self.goal_object, str)
            or self.goal_object not in self.objects
        ):
            print(f"Level does not have goal object")
            return False

        # Check if the level has action objects
        if (
            self.action_objects is None
            or not isinstance(self.action_objects, list)
            or len(self.action_objects) == 0
        ):
            print(f"Level does not have action objects")
            return False

        # Check if name is present
        if self.name is None or self.name == "empty_task":
            print(f"Level does not have a name")
            return False

        # Check if description is present
        if (
            self.description is None
            or self.description
            == "This is the base class for tasks, do not use this as-is!"
        ):
            print(f"Level does not have a description")
            return False

        # Check if ranges of all objects are valid
        for name, obj in self.objects.items():
            if (
                not isinstance(obj, Ball)
                and not isinstance(obj, Basket)
                and not isinstance(obj, Platform)
            ):
                print(
                    f"Object {name} should be a Ball, Basket, or Platform: {type(obj)} is not valid"
                )
                return False
            if obj.x < -5 or obj.x > 5:
                print(f"Object {name} has an x coordinate outside of the range [-5, 5]")
                return False
            if obj.y < -5 or obj.y > 5:
                print(f"Object {name} has a y coordinate outside of the range [-5, 5]")
                return False
            if not isinstance(obj.dynamic, bool):
                print(f"Object {name} has a dynamic attribute that is not a boolean")
                return False
            if obj.color not in system_colors:
                print(f"Object {name} has an invalid color: {obj.color}")
                return False
            if isinstance(obj, Ball):
                if obj.radius < 0.1 or obj.radius > 5:
                    print(
                        f"Object {name} has a radius outside of the range [0.1, 5] (this is not a valid ball)"
                    )
                    return False
            if isinstance(obj, Basket):
                if obj.scale < 0.1 or obj.scale > 5:
                    print(
                        f"Object {name} has a scale outside of the range [0.1, 5] (this is not a valid basket)"
                    )
                    return False
            if isinstance(obj, Platform):
                if obj.length < 0.1 or obj.length > 10:
                    print(
                        f"Object {name} has a length outside of the range [0.1, 10] (this is not a valid platform)"
                    )
                    return False
                if obj.angle < -360 or obj.angle > 360:
                    print(
                        f"Object {name} has an angle outside of the range [-360, 360] (this is not a valid platform)"
                    )
                    return False
        return True
