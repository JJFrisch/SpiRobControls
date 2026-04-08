# Isaac Lab Setup Guide for Two-Cable SpiRob

## 1. System Requirements & Installation

### Prerequisites
```bash
# Ubuntu 20.04/22.04 or Windows with WSL2
# NVIDIA GPU with CUDA support
# Python 3.8-3.10

# Check your CUDA version
nvidia-smi
```

### Step 1: Install Isaac Sim
```bash
# Download Isaac Sim from NVIDIA Developer Portal
# https://developer.nvidia.com/isaac-sim
# Install via Omniverse Launcher (recommended) or standalone

# For headless servers, use:
wget https://developer.nvidia.com/isaac-sim-app--isaacsim_version_info
# Follow NVIDIA's installation guide
```

### Step 2: Clone and Install Isaac Lab
```bash
# Clone Isaac Lab repository
git clone https://github.com/isaac-sim/IsaacLab.git
cd IsaacLab

# Create conda environment
conda create -n isaaclab python=3.10
conda activate isaaclab

# Install Isaac Lab
./isaaclab.sh --install

# Verify installation
./isaaclab.sh -p source/standalone/tutorials/00_sim/create_empty.py
```

## 2. Project Structure Setup

Create your spirob project structure:

```
IsaacLab/
├── source/extensions/omni.isaac.lab_tasks/
│   └── omni/isaac/lab_tasks/
│       └── manager_based/
│           └── manipulation/
│               └── spirob/
│                   ├── __init__.py
│                   ├── spirob_env.py
│                   ├── spirob_env_cfg.py
│                   └── assets/
│                       ├── spirob_body.stl
│                       ├── spool.stl
│                       ├── motor_mount.stl
│                       └── spirob.usd
└── source/standalone/workflows/
    └── spirob/
        ├── train_spirob.py
        └── play_spirob.py
```

## 3. Asset Preparation

### Step 1: STL to USD Conversion

First, create the USD asset from your STLs:

```python
# source/extensions/omni.isaac.lab_tasks/scripts/convert_spirob_assets.py
import omni
from pxr import UsdGeom, Usd, UsdPhysics, UsdShade, Sdf, Gf
import omni.usd
import omni.kit.commands

def create_spirob_usd():
    """Convert STL files to USD with proper physics properties"""
    
    # Create new stage
    stage = omni.usd.get_context().new_stage()
    
    # Set up scene
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
    scene = UsdPhysics.Scene.Define(stage, "/physicsScene")
    scene.CreateGravityDirectionAttr().Set(Gf.Vec3f(0.0, 0.0, -1.0))
    scene.CreateGravityMagnitudeAttr().Set(981.0)  # cm/s^2
    
    # Create main spirob assembly
    spirob_prim = UsdGeom.Xform.Define(stage, "/SpiRob")
    
    # Import STL files and create rigid bodies
    create_spirob_body(stage)
    create_spools(stage)
    create_motor_mounts(stage)
    create_cables(stage)
    
    # Save USD file
    stage.GetRootLayer().Export("assets/spirob.usd")
    print("SpiRob USD asset created successfully!")

def create_spirob_body(stage):
    """Create the main spirob body from STL"""
    
    # Import STL mesh
    omni.kit.commands.execute(
        "CreateMeshFromFile",
        mesh_path="/path/to/your/spirob_body.stl",
        prim_path="/SpiRob/Body"
    )
    
    # Get the prim and add physics
    body_prim = stage.GetPrimAtPath("/SpiRob/Body")
    
    # Add rigid body physics
    rigid_body_api = UsdPhysics.RigidBodyAPI.Apply(body_prim)
    mass_api = UsdPhysics.MassAPI.Apply(body_prim)
    mass_api.CreateMassAttr(0.05)  # 50g in kg
    
    # Add collision shape
    collision_api = UsdPhysics.CollisionAPI.Apply(body_prim)
    
    # Set material properties
    create_spirob_material(stage, body_prim)

def create_spools(stage):
    """Create motor spools from STL"""
    
    for i, side in enumerate(["Left", "Right"]):
        spool_path = f"/SpiRob/Spool_{side}"
        
        # Import spool STL
        omni.kit.commands.execute(
            "CreateMeshFromFile",
            mesh_path="/path/to/your/spool.stl",
            prim_path=spool_path
        )
        
        # Position spools at anchor points
        spool_prim = stage.GetPrimAtPath(spool_path)
        xform = UsdGeom.Xformable(spool_prim)
        
        if side == "Left":
            xform.AddTranslateOp().Set(Gf.Vec3d(-200, 0, 100))  # Left anchor
        else:
            xform.AddTranslateOp().Set(Gf.Vec3d(200, 0, 100))   # Right anchor
        
        # Add physics - spools are kinematic (motor controlled)
        rigid_body_api = UsdPhysics.RigidBodyAPI.Apply(spool_prim)
        rigid_body_api.CreateKinematicEnabledAttr(True)

def create_cables(stage):
    """Create cable representations using deformable bodies"""
    
    # For now, we'll use constraint-based cables
    # Isaac Lab has good support for cable simulation
    
    # Left cable
    left_cable = UsdGeom.Xform.Define(stage, "/SpiRob/Cable_Left")
    # Right cable  
    right_cable = UsdGeom.Xform.Define(stage, "/SpiRob/Cable_Right")
    
    # Cable physics will be handled in the environment configuration

def create_spirob_material(stage, prim):
    """Create physics material for spirob"""
    
    # Create physics material
    material_path = "/SpiRob/Materials/SpirRobMaterial"
    material = UsdShade.Material.Define(stage, material_path)
    
    # Physics properties
    physics_material = UsdPhysics.MaterialAPI.Apply(material.GetPrim())
    physics_material.CreateStaticFrictionAttr(0.5)
    physics_material.CreateDynamicFrictionAttr(0.3)
    physics_material.CreateRestitutionAttr(0.1)
    
    # Bind material to prim
    binding_api = UsdShade.MaterialBindingAPI.Apply(prim)
    binding_api.Bind(material)

if __name__ == "__main__":
    create_spirob_usd()
```

### Step 2: Run Asset Conversion

```bash
# Navigate to Isaac Lab directory
cd IsaacLab

# Run the conversion script
./isaaclab.sh -p source/extensions/omni.isaac.lab_tasks/scripts/convert_spirob_assets.py
```

## 4. Environment Configuration

Create the main environment configuration:

```python
# source/extensions/omni.isaac.lab_tasks/omni/isaac/lab_tasks/manager_based/manipulation/spirob/spirob_env_cfg.py

import omni.isaac.lab.sim as sim_utils
from omni.isaac.lab.assets import ArticulationCfg, AssetBaseCfg
from omni.isaac.lab.envs import ManagerBasedRLEnvCfg
from omni.isaac.lab.managers import CurriculumTermCfg as CurrTerm
from omni.isaac.lab.managers import EventTermCfg as EventTerm
from omni.isaac.lab.managers import ObservationGroupCfg as ObsGroup
from omni.isaac.lab.managers import ObservationTermCfg as ObsTerm
from omni.isaac.lab.managers import RewardTermCfg as RewTerm
from omni.isaac.lab.managers import SceneEntityCfg
from omni.isaac.lab.managers import TerminationTermCfg as DoneTerm
from omni.isaac.lab.scene import InteractiveSceneCfg
from omni.isaac.lab.sensors import ContactSensorCfg, RayCasterCfg, patterns
from omni.isaac.lab.terrains import TerrainImporterCfg
from omni.isaac.lab.utils import configclass
from omni.isaac.lab.utils.assets import ISAAC_NUCLEUS_DIR
from omni.isaac.lab.utils.noise import AdditiveUniformNoiseCfg as Unoise

import omni.isaac.lab_tasks.manager_based.manipulation.spirob.mdp as mdp

##
# Pre-defined configs
##
from omni.isaac.lab_assets.franka import FRANKA_PANDA_CFG  # We'll modify this

@configclass
class SpiRobEnvCfg(ManagerBasedRLEnvCfg):
    """Configuration for the SpiRob environment."""

    # Scene settings
    episode_length_s = 10.0
    decimation = 2
    num_actions = 2  # Left and right motor speeds
    num_observations = 12  # Position, velocity, cable lengths, target info
    num_states = 0

    # Simulation settings
    sim: sim_utils.SimulationCfg = sim_utils.SimulationCfg(
        dt=1.0 / 120.0,  # 120 Hz simulation
        render_interval=decimation,
        disable_contact_processing=True,
        physics_material=sim_utils.RigidBodyMaterialCfg(
            friction_combine_mode="multiply",
            restitution_combine_mode="multiply",
            static_friction=1.0,
            dynamic_friction=1.0,
        ),
    )

    # Ground plane
    terrain = TerrainImporterCfg(
        prim_path="/World/ground",
        terrain_type="plane",
        collision_group=-1,
        physics_material=sim_utils.RigidBodyMaterialCfg(
            friction_combine_mode="multiply",
            restitution_combine_mode="multiply",
            static_friction=1.0,
            dynamic_friction=1.0,
            restitution=0.0,
        ),
        debug_vis=False,
    )

    # Scene
    scene: InteractiveSceneCfg = InteractiveSceneCfg(
        num_envs=4096, env_spacing=4.0, replicate_physics=True
    )

    # SpiRob robot configuration
    spirob: ArticulationCfg = ArticulationCfg(
        prim_path="{ENV_REGEX_NS}/SpiRob",
        spawn=sim_utils.UsdFileCfg(
            usd_path="assets/spirob.usd",  # Your converted USD file
            rigid_props=sim_utils.RigidBodyPropertiesCfg(
                disable_gravity=False,
                retain_accelerations=False,
                linear_damping=0.0,
                angular_damping=0.0,
                max_linear_velocity=1000.0,
                max_angular_velocity=1000.0,
                max_depenetration_velocity=1.0,
            ),
            articulation_props=sim_utils.ArticulationRootPropertiesCfg(
                enabled_self_collisions=True,
                solver_position_iteration_count=8,
                solver_velocity_iteration_count=0,
            ),
        ),
        init_state=ArticulationCfg.InitialStateCfg(
            pos=(0.0, 0.0, 0.5),  # Start position
            joint_pos={".*": 0.0},  # All joints start at 0
            joint_vel={".*": 0.0},
        ),
        actuators={
            "motors": sim_utils.DCMotorCfg(
                joint_names_expr=["left_motor", "right_motor"],
                effort_limit=10.0,  # Adjust based on your motors
                velocity_limit=100.0,
                stiffness=0.0,  # Direct velocity control
                damping=0.1,
            ),
        },
    )

    # Target objects to collect
    target_object: AssetBaseCfg = AssetBaseCfg(
        prim_path="{ENV_REGEX_NS}/TargetObject",
        spawn=sim_utils.SphereCfg(
            radius=0.025,  # 2.5cm radius
            rigid_props=sim_utils.RigidBodyPropertiesCfg(
                kinematic_enabled=False,
            ),
            mass_props=sim_utils.MassPropertiesCfg(mass=0.01),  # 10g
            collision_props=sim_utils.CollisionPropertiesCfg(),
            visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(1.0, 0.0, 0.0)),
        ),
        init_state=AssetBaseCfg.InitialStateCfg(
            pos=(0.0, 0.0, 0.1),  # Will be randomized
        ),
    )

    # Sensors
    contact_forces = ContactSensorCfg(
        prim_path="{ENV_REGEX_NS}/SpiRob/Body", 
        update_period=0.0,
        track_pose=False,
    )

    # Observations
    observations: ObsGroup = ObsGroup({
        "policy": ObsGroup({
            # SpiRob state
            "spirob_pos": ObsTerm(func=mdp.spirob_position),
            "spirob_vel": ObsTerm(func=mdp.spirob_velocity),
            "cable_lengths": ObsTerm(func=mdp.cable_lengths),
            "cable_tensions": ObsTerm(func=mdp.cable_tensions),
            
            # Target information
            "target_pos": ObsTerm(func=mdp.target_position),
            "target_distance": ObsTerm(func=mdp.distance_to_target),
        })
    })

    # Actions (motor velocities)
    actions: ActionsCfg = ActionsCfg()

    # Rewards
    rewards: RewardsCfg = RewardsCfg({
        # Main objective: get close to target
        "distance_reward": RewTerm(
            func=mdp.distance_to_target_reward,
            weight=2.0,
        ),
        
        # Collection bonus
        "collection_bonus": RewTerm(
            func=mdp.target_collection_bonus,
            weight=10.0,
        ),
        
        # Penalty for large actions (energy efficiency)
        "action_penalty": RewTerm(
            func=mdp.action_rate_l2,
            weight=-0.01,
        ),
        
        # Penalty for hitting boundaries
        "boundary_penalty": RewTerm(
            func=mdp.boundary_penalty,
            weight=-1.0,
        ),
    })

    # Termination conditions
    terminations: TerminationsCfg = TerminationsCfg({
        "time_out": DoneTerm(func=mdp.time_out, time_out=True),
        "target_collected": DoneTerm(func=mdp.target_collected),
        "spirob_out_of_bounds": DoneTerm(func=mdp.spirob_out_of_bounds),
    })

    # Events (for randomization and curriculum)
    events: EventsCfg = EventsCfg({
        "reset_target_position": EventTerm(
            func=mdp.reset_target_position,
            mode="reset",
        ),
        "reset_spirob_state": EventTerm(
            func=mdp.reset_spirob_state,
            mode="reset",
        ),
    })

##
# Action and other configurations
##

@configclass
class ActionsCfg:
    """Action configuration for SpiRob environment."""
    joint_vel = mdp.JointVelocityActionCfg(
        asset_name="spirob",
        joint_names=["left_motor", "right_motor"],
        scale=100.0,  # Max motor speed
    )

@configclass 
class RewardsCfg:
    """Reward configuration for SpiRob environment."""
    pass

@configclass
class TerminationsCfg:
    """Termination configuration for SpiRob environment."""
    pass

@configclass
class EventsCfg:
    """Event configuration for SpiRob environment."""
    pass
```

## 5. MDP (Markov Decision Process) Functions

Create the core RL functions:

```python
# source/extensions/omni.isaac.lab_tasks/omni/isaac/lab_tasks/manager_based/manipulation/spirob/mdp/__init__.py

from omni.isaac.lab.envs.mdp import *  # noqa: F401, F403

from .actions import *  # noqa: F401, F403
from .commands import *  # noqa: F401, F403
from .curriculums import *  # noqa: F401, F403
from .events import *  # noqa: F401, F403
from .observations import *  # noqa: F401, F403
from .rewards import *  # noqa: F401, F403
from .terminations import *  # noqa: F401, F403
```

```python
# source/extensions/omni.isaac.lab_tasks/omni/isaac/lab_tasks/manager_based/manipulation/spirob/mdp/observations.py

from __future__ import annotations

import torch
from typing import TYPE_CHECKING

import omni.isaac.lab.utils.math as math_utils
from omni.isaac.lab.assets import ArticulationData
from omni.isaac.lab.managers import SceneEntityCfg
from omni.isaac.lab.sensors import ContactSensorData

if TYPE_CHECKING:
    from omni.isaac.lab.envs import ManagerBasedRLEnv

def spirob_position(env: ManagerBasedRLEnv, asset_cfg: SceneEntityCfg) -> torch.Tensor:
    """SpiRob body position in world frame."""
    asset: Articulation = env.scene[asset_cfg.name]
    return asset.data.root_pos_w[:, :2]  # Only X, Y position

def spirob_velocity(env: ManagerBasedRLEnv, asset_cfg: SceneEntityCfg) -> torch.Tensor:
    """SpiRob body velocity in world frame.""" 
    asset: Articulation = env.scene[asset_cfg.name]
    return asset.data.root_lin_vel_w[:, :2]  # Only X, Y velocity

def cable_lengths(env: ManagerBasedRLEnv, asset_cfg: SceneEntityCfg) -> torch.Tensor:
    """Current cable lengths based on spool positions."""
    asset: Articulation = env.scene[asset_cfg.name]
    
    # Get spool positions (joint positions converted to cable length)
    joint_pos = asset.data.joint_pos
    
    # Convert motor rotations to cable lengths
    # Assuming joint positions are in radians, spool radius is 1cm
    spool_radius = 0.01  # 1cm in meters
    cable_lengths = joint_pos * spool_radius
    
    return cable_lengths

def cable_tensions(env: ManagerBasedRLEnv, asset_cfg: SceneEntityCfg) -> torch.Tensor:
    """Estimate cable tensions from joint efforts."""
    asset: Articulation = env.scene[asset_cfg.name]
    return asset.data.applied_torque

def target_position(env: ManagerBasedRLEnv, asset_cfg: SceneEntityCfg) -> torch.Tensor:
    """Target object position."""
    asset = env.scene[asset_cfg.name]
    return asset.data.root_pos_w[:, :2]  # Only X, Y

def distance_to_target(env: ManagerBasedRLEnv) -> torch.Tensor:
    """Distance from SpiRob to target object."""
    spirob_pos = env.scene["spirob"].data.root_pos_w[:, :2]
    target_pos = env.scene["target_object"].data.root_pos_w[:, :2]
    
    return torch.norm(target_pos - spirob_pos, dim=1, keepdim=True)
```

```python
# source/extensions/omni.isaac.lab_tasks/omni/isaac/lab_tasks/manager_based/manipulation/spirob/mdp/rewards.py

from __future__ import annotations

import torch
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from omni.isaac.lab.envs import ManagerBasedRLEnv

def distance_to_target_reward(env: ManagerBasedRLEnv) -> torch.Tensor:
    """Reward for getting close to the target."""
    spirob_pos = env.scene["spirob"].data.root_pos_w[:, :2]
    target_pos = env.scene["target_object"].data.root_pos_w[:, :2]
    
    distance = torch.norm(target_pos - spirob_pos, dim=1)
    
    # Exponential reward for getting closer
    reward = torch.exp(-distance * 5.0)  # Scale factor of 5
    
    return reward

def target_collection_bonus(env: ManagerBasedRLEnv) -> torch.Tensor:
    """Large bonus for collecting the target."""
    collection_radius = 0.05  # 5cm collection radius
    
    spirob_pos = env.scene["spirob"].data.root_pos_w[:, :2]  
    target_pos = env.scene["target_object"].data.root_pos_w[:, :2]
    
    distance = torch.norm(target_pos - spirob_pos, dim=1)
    collected = distance < collection_radius
    
    return collected.float() * 100.0  # Large bonus

def action_rate_l2(env: ManagerBasedRLEnv) -> torch.Tensor:
    """Penalty for large motor actions (energy efficiency)."""
    actions = env.action_manager.action
    return torch.sum(torch.square(actions), dim=1)

def boundary_penalty(env: ManagerBasedRLEnv) -> torch.Tensor:
    """Penalty for going out of bounds."""
    spirob_pos = env.scene["spirob"].data.root_pos_w
    
    # Define boundaries (adjust to your workspace)
    x_limit = 2.0  # meters
    y_limit = 2.0  # meters
    z_min = 0.1   # minimum height
    
    out_of_bounds = (
        (torch.abs(spirob_pos[:, 0]) > x_limit) |
        (torch.abs(spirob_pos[:, 1]) > y_limit) |
        (spirob_pos[:, 2] < z_min)
    )
    
    return out_of_bounds.float() * -10.0  # Penalty
```

## 6. Training Script

Create the main training script:

```python
# source/standalone/workflows/spirob/train_spirob.py

"""Script to train RL policy for SpiRob manipulation."""

import argparse
import torch
from omni.isaac.lab.app import AppLauncher

# Parse arguments
parser = argparse.ArgumentParser(description="Train SpiRob manipulation policy")
parser.add_argument("--num_envs", type=int, default=4096, help="Number of environments")
parser.add_argument("--task", type=str, default="Isaac-SpiRob-v0", help="Task name")
parser.add_argument("--seed", type=int, default=42, help="Random seed")
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()

# Launch omniverse app
app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

"""Rest of the imports and training code."""

from omni.isaac.lab.envs import ManagerBasedRLEnvCfg
from omni.isaac.lab_tasks.utils import register_env

# Import SpiRob environment
from omni.isaac.lab_tasks.manager_based.manipulation.spirob import SpiRobEnvCfg

# Register environment
register_env("Isaac-SpiRob-v0", SpiRobEnvCfg)

def main():
    """Main training function."""
    
    # Create environment configuration
    env_cfg = SpiRobEnvCfg()
    env_cfg.scene.num_envs = args_cli.num_envs
    
    # Create environment
    env = gym.make(args_cli.task, cfg=env_cfg)
    
    # Initialize RL algorithm (using RL-Games or Stable-Baselines3)
    from omni.isaac.lab_tasks.utils.wrappers.rl_games import RlGamesVecEnvWrapper
    
    env = RlGamesVecEnvWrapper(env)
    
    # Training configuration
    train_cfg = {
        "seed": args_cli.seed,
        "algo": {
            "name": "a2c_continuous",
        },
        "model": {
            "name": "continuous_a2c_logstd",
        },
        "network": {
            "name": "actor_critic",
            "separate": False,
            "mlp": {
                "units": [256, 128, 64],
                "activation": "elu",
            }
        },
        "config": {
            "name": "SpiRob",
            "env_name": "rlgpu",
            "multi_gpu": False,
            "ppo": True,
            "mixed_precision": True,
            "normalize_input": True,
            "normalize_value": True,
            "value_bootstrap": True,
            "num_actors": env_cfg.scene.num_envs,
            "reward_shaper": {
                "scale_value": 1.0,
            },
            "normalize_advantage": True,
            "gamma": 0.99,
            "tau": 0.95,
            "learning_rate": 3e-4,
            "lr_schedule": None,
            "score_to_win": 20000,
            "max_epochs": 2000,
            "save_best_after": 100,
            "save_frequency": 50,
            "grad_norm": 1.0,
            "entropy_coef": 0.0,
            "truncate_grads": True,
            "e_clip": 0.2,
            "horizon_length": 32,
            "minibatch_size": 32768,
            "mini_epochs": 8,
            "critic_coef": 4,
            "clip_value": True,
            "seq_len": 4,
            "bounds_loss_coef": 0.0001,
        }
    }
    
    # Start training
    from rl_games.common import env_configurations, vecenv
    from rl_games.torch_runner import Runner
    
    # Register environment
    vecenv.register('rlgpu', lambda config_name, num_actors, **kwargs: env)
    env_configurations.register('rlgpu', {
        'vecenv_type': 'rlgpu',
        'env_creator': lambda **kwargs: env,
    })
    
    # Create and run trainer
    runner = Runner()
    runner.load(train_cfg)
    runner.run({
        "train": True,
        "play": False,
        "checkpoint": "",
        "sigma": None
    })

if __name__ == "__main__":
    main()
    simulation_app.close()
```

## 7. Running Your Setup

### Test the Environment
```bash
# Navigate to Isaac Lab
cd IsaacLab

# Test basic environment creation
./isaaclab.sh -p source/standalone/workflows/spirob/train_spirob.py --num_envs 64

# For headless training (no GUI)
./isaaclab.sh -p source/standalone/workflows/spirob/train_spirob.py --headless
```

### Monitor Training
```bash
# Training logs will be saved to logs/
# Use tensorboard to monitor progress
tensorboard --logdir logs/

# Or use wandb integration (add to train config)
```

## 8. Next Steps

1. **Fine-tune physics parameters** in your USD file to match real robot
2. **Implement domain randomization** for sim-to-real transfer
3. **Add camera observations** for vision-based learning
4. **Create curriculum learning** to progressively increase difficulty
5. **Test policies on real robot** using the same action/observation interface

## Common Issues & Solutions

- **STL import issues**: Use Blender or MeshLab to clean meshes before import
- **Physics instability**: Reduce simulation timestep, increase solver iterations
- **Memory issues**: Reduce num_envs, use mixed precision training
- **Slow training**: Enable GPU acceleration, optimize observation functions

This setup provides a complete foundation for training your SpiRob with RL in Isaac Lab!