# rl_utils.py
import numpy as np
from spirob_params import ROBOT_PARAMS

def scale_action(action_normalized):
    """Convert normalized [-1, 1] actions to actual cable lengths."""
    min_len = ROBOT_PARAMS["min_cable_length"]
    max_len = ROBOT_PARAMS["max_cable_length"]
    return min_len + (action_normalized + 1) * (max_len - min_len) / 2

def normalize_action(actual_lengths):
    """Convert cable lengths to normalized [-1, 1] actions."""
    min_len = ROBOT_PARAMS["min_cable_length"]
    max_len = ROBOT_PARAMS["max_cable_length"]
    return 2 * (actual_lengths - min_len) / (max_len - min_len) - 1

def reward_reach(target_pos, end_effector_pos):
    """Negative distance between EE and target."""
    return -np.linalg.norm(target_pos - end_effector_pos)

def reward_grasp(object_pos, ee_pos, grasp_radius=0.05):
    """Binary reward if within grasp radius."""
    distance = np.linalg.norm(object_pos - ee_pos)
    return 1.0 if distance < grasp_radius else -distance

class EpisodeStats:
    def __init__(self):
        self.reset()

    def reset(self):
        self.total_reward = 0
        self.length = 0

    def update(self, reward):
        self.total_reward += reward
        self.length += 1

# Model consistency check

def validate_models(mujoco_params, isaac_params):
    """Validate parameter consistency across simulation platforms."""
    mismatches = []

    for key in ROBOT_PARAMS:
        mujoco_val = mujoco_params.get(key)
        isaac_val = isaac_params.get(key)
        if not np.allclose(mujoco_val, isaac_val, atol=1e-6):
            mismatches.append(f"Mismatch in '{key}': MuJoCo={mujoco_val}, Isaac={isaac_val}")

    if mismatches:
        print("Model consistency check FAILED:")
        for m in mismatches:
            print(" -", m)
        return False
    else:
        print("Model consistency check PASSED.")
        return True


def load_isaac_params_and_validate(yaml_path):
    isaac_params = load_params_from_yaml(yaml_path)
    return validate_models(ROBOT_PARAMS, isaac_params)

