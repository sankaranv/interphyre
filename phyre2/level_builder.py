import json
import os
from phyre2.utils import Ball, Basket, Platform
from phyre2.environment import PHYREWorld, PHYRELevel
import numpy as np
import yaml


class PHYRETemplate:
    def __init__(self, template_name, template_path="templates/"):
        """
        Initializes the template
        Args:
            template_name:
            template_path:

        Returns:

        """
        self.template = self.load_template(template_name, template_path)

    def load_template(self, template_name, template_path="templates/"):
        """
        Loads the template from file
        Args:
            template_name:
            template_path:

        Returns:

        """
        template = json.load(
            open(os.path.join(template_path, f"{template_name}.json"), "r")
        )
        if not self.is_valid_template(template):
            raise ValueError("Template is not valid, cannot load")
        return template

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
        if not self.is_valid_template(self.template):
            raise ValueError("Template is not valid, cannot create level")

        # Create the level
        level = {
            "name": level_name,
            "objects": {},
            "target_object": self.template["target_object"],
            "goal_object": self.template["goal_object"],
            "action_objects": self.template["action_objects"],
        }

        for name, obj in self.template["objects"].items():
            # Create object
            level_obj = {"dynamic": obj["dynamic"], "type": obj["type"]}

            # Set the fixed attributes
            for attribute, value in obj["fixed_attributes"].items():
                level_obj[attribute] = value

            # Sample random values for the variable attributes
            # TODO - this only supports continuous real values, need to generalize this
            for attribute, value_range in obj["ranges"].items():
                value = np.random.uniform(value_range[0], value_range[1])
                level_obj[attribute] = value
            level["objects"][name] = level_obj

        # Test if the level is valid
        if not self.is_valid_level(level):
            return None

        # Test if the level can be solved
        if check_solvable:
            solution = self.solve_level(level, max_trials=100)
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
        level_path="levels/",
    ):
        """
        Generates levels from the template
        Args:
            template:
            num_levels:
            check_solvable:
            save_to_file:
            level_path:

        Returns:

        """
        # Check if the template is valid
        if not self.is_valid_template(self.template):
            raise ValueError("Template is not valid, cannot generate levels")

        # Generate levels
        levels = []
        for i in range(num_levels):
            level_name = f"{self.template['name']}_{i+1}"
            level = self.create_level(level_name, self.template, check_solvable)
            if level:
                levels.append(level)
            else:
                i -= 1
        if save_to_file:
            for level in levels:
                self.write_level_to_file(level, self.template["name"], level_path)
        return levels

    def write_level_to_file(self, level, template_name, level_path):
        """
        Writes the level to file
        Args:
            level:
            template_name:
            level_path:

        Returns: None

        """
        if not os.path.exists(os.path.join(level_path, template_name)):
            os.makedirs(os.path.join(level_path, template_name))
        json.dump(
            level,
            open(os.path.join(level_path, template_name, f"{level['name']}.json"), "w"),
            indent=4,
        )

    def write_template_to_file(self, template_path):
        """
        Writes the template to file
        Args:
            template:
            template_path:

        Returns: None

        """
        # Check if the template is valid
        if not self.is_valid_template(self.template):
            raise ValueError("Template is not valid, cannot write to file")

        template_name = self.template["name"]
        if not os.path.exists(template_path):
            os.makedirs(template_path)
        json.dump(
            self.template,
            open(os.path.join(template_path, f"{template_name}.json"), "w"),
            indent=4,
        )

    def is_valid_level(self, level):
        """
        Checks if the level is valid
          Args:
              level:
        Returns: True if the level is valid, False otherwise
        """

        # Check if the level is a dictionary
        if not isinstance(level, dict):
            print("Level is not a dictionary")
            return False
        if "name" not in level:
            print("Level does not have a name")
            return False

        name = level["name"]
        if "objects" not in level:
            print(f"Level {name} does not have any objects")
            return False
        elif "target_object" not in level:
            print(f"Level {name} does not have a target object")
            return False
        elif "goal_object" not in level:
            print(f"Level {name} does not have a goal object")
            return False
        elif "action_objects" not in level:
            print(f"Level {name} does not have any action objects")
            return False
        elif level["target_object"] not in level["objects"]:
            target_object = level["target_object"]
            print(f"Target object {target_object} not found in level {name}")
            return False
        elif level["goal_object"] not in level["objects"]:
            goal_object = level["goal_object"]
            print(f"Goal object {goal_object} not found in level {name}")
            return False
        else:
            for action_object in level["action_objects"]:
                if action_object not in level["objects"]:
                    print(f"Action {action_object} not found in level")
                    return False

        return True

    def is_valid_template(self, template):
        """
        Checks if the template is valid
        Args:
            template:

        Returns: True if the template is valid, False otherwise
        """

        # Check if the template is a dictionary
        if not isinstance(template, dict):
            print("Template is not a dictionary")
            return False

        # Check if the template has a name
        if "name" not in template:
            print("Template does not have a name")
            return False

        # Check if the template has a description
        if "description" not in template:
            print("Template does not have a description")
            return False

        # Check if the template has at least one action object
        if "action_objects" not in template:
            print("Template does not have any action objects")
            return False

        # Check if the template has at least one target object
        if "target_object" not in template:
            print("Template does not have a target object")
            return False

        # Check if the template has at least one goal object
        if "goal_object" not in template:
            print("Template does not have a goal object")
            return False

        # Check if the template has at least one object
        if "objects" not in template or len(template["objects"]) == 0:
            print("Template does not have any objects")
            return False

        for name, obj in template["objects"].items():
            if "type" not in obj:
                print(f"Object {name} does not have a type")
                return False
            if "dynamic" not in obj:
                print(f"Object {name} does not have a dynamic attribute")
                return False
            if "fixed_attributes" not in obj:
                print(f"Object {name} does not have fixed attributes")
                return False
            if "ranges" not in obj:
                print(f"Object {name} does not have ranges")
                return False

            # Obtain list of fixed and variable attributes in the template as well as the true object attributes
            template_attributes = (
                list(obj["fixed_attributes"].keys())
                + list(obj["ranges"].keys())
                + ["dynamic"]
            )
            if obj["type"] == "ball":
                object_attributes = list(Ball.__annotations__.keys())
            elif obj["type"] == "basket":
                object_attributes = list(Basket.__annotations__.keys())
            elif obj["type"] == "platform":
                object_attributes = list(Platform.__annotations__.keys())
            else:
                raise ValueError(f"Object type {obj['type']} not supported")

            # Check if the object has all the required attributes
            for attribute in object_attributes:
                if attribute not in template_attributes:
                    return False

            # Check if the object has any extra attributes
            for attribute in template_attributes:
                if attribute not in object_attributes:
                    return False

        return True
