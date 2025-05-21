# spirob_params.py
import numpy as np

# Anchor points for cables
ANCHOR_POINTS = {
    "base": np.array([
        [0.1, 0.0, 0.0],
        [-0.05, 0.0866, 0.0],
        [-0.05, -0.0866, 0.0],
    ]),
    "end_effector": np.array([
        [0.05, 0.0, 0.0],
        [-0.025, 0.0433, 0.0],
        [-0.025, -0.0433, 0.0],
    ]),
}

# Robot physical parameters
ROBOT_PARAMS = {
    "mass": 0.2,               # kg
    "radius": 0.05,            # m
    "height": 0.02,            # m
    "max_cable_length": 0.3,   # m
    "min_cable_length": 0.1,   # m
}

# Cable actuation constraints
ACTUATION_LIMITS = {
    "max_pull_speed": 0.01,    # m/s
    "max_force": 5.0,          # N
}

def load_params_from_yaml(yaml_path):
    with open(yaml_path, 'r') as f:
        data = yaml.safe_load(f)
    return data
