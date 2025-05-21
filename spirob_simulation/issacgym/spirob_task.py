import math
import numpy as np
import os
import torch
import yaml

from isaacgym import gymtorch
from isaacgym import gymapi
from isaacgym.torch_utils import *

from isaacgymenvs.tasks.base.vec_task import VecTask


class SpiRobTask(VecTask):
    def __init__(self, cfg, rl_device, sim_device, graphics_device_id, headless, virtual_screen_capture, force_render):
        """
        Initialize the SpiRob task for Isaac Gym.
        """
        self.cfg = cfg
        
        # Load task-specific configuration
        config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
        with open(config_path, 'r') as f:
            self.task_config = yaml.safe_load(f)

        # Default parameters
        self.max_episode_length = self.task_config.get("max_episode_steps", 500)
        self.grasp_threshold = self.task_config.get("grasp_threshold", 0.025)
        self.lift_height = self.task_config.get("lift_height", 0.08)
        
        # Distance reward scale
        self.distance_reward_scale = self.task_config.get("distance_reward_scale", 10.0)
        self.grasp_reward = self.task_config.get("grasp_reward", 10.0)
        self.lift_reward = self.task_config.get("lift_reward", 50.0)
        self.tension_penalty = self.task_config.get("tension_penalty", 0.1)
        self.time_penalty = self.task_config.get("time_penalty", 0.1)
        
        # Actions and observations
        self.num_actions = 3  # 3 cable motors
        self.num_observations = 13  # Same as MuJoCo version
        
        # For tracking cable tensions
        self.cable_forces = torch.zeros((self.cfg["env"]["numEnvs"], 3), device=self.cfg["sim_device"])
        self.cable_lengths = torch.zeros((self.cfg["env"]["numEnvs"], 3), device=self.cfg["sim_device"])

        # Initialize base class
        super().__init__(
            config=self.cfg,
            rl_device=rl_device,
            sim_device=sim_device,
            graphics_device_id=graphics_device_id,
            headless=headless,
            virtual_screen_capture=virtual_screen_capture,
            force_render=force_render
        )

    def create_sim(self):
        """Create simulation instance and environments."""
        # Set simulation parameters
        self.sim_params.substeps = self.task_config.get("substeps", 10)
        self.sim_params.dt = 0.01
        self.sim_params.up_axis = gymapi.UP_AXIS_Z
        self.sim_params.gravity = gymapi.Vec3(0.0, 0.0, -9.81)
        
        # Set physics parameters
        self.sim_params.physx.solver_type = 1
        self.sim_params.physx.num_position_iterations = 4
        self.sim_params.physx.num_velocity_iterations = 1
        self.sim_params.physx.contact_offset = 0.01
        self.sim_params.physx.rest_offset = 0.0
        
        # Create simulation
        self.sim = self.gym.create_sim(
            self.sim_device_id, self.graphics_device_id, self.physics_engine, self.sim_params)
        
        # Create ground plane
        plane_params = gymapi.PlaneParams()
        plane_params.normal = gymapi.Vec3(0, 0, 1)
        self.gym.add_ground(self.sim, plane_params)
        
        # Load assets
        asset_root = os.path.join(os.path.dirname(__file__), "assets")
        spirob_asset_file = "spirob.urdf"
        object_asset_file = "target_object.urdf"
        
        # Set up asset options
        asset_options = gymapi.AssetOptions()
        asset_options.fix_base_link = True
        asset_options.armature = 0.01
        
        # Load robot asset
        print("Loading SpiRob asset...")
        spirob_asset = self.gym.load_asset(self.sim, asset_root, spirob_asset_file, asset_options)
        
        # Load object asset
        print("Loading target object asset...")
        object_asset_options = gymapi.AssetOptions()
        object_asset_options.density = 200.0
        self.object_asset = self.gym.load_asset(self.sim, asset_root, object_asset_file, object_asset_options)
        
        # Set up environments
        print(f"Creating {self.num_envs} environments...")
        num_per_row = int(math.sqrt(self.num_envs))
        spacing = 1.0
        env_lower = gymapi.Vec3(-spacing, -spacing, 0.0)
        env_upper = gymapi.Vec3(spacing, spacing, spacing)
        
        self.spirob_handles = []
        self.object_handles = []
        self.envs = []
        
        for i in range(self.num_envs):
            # Create environment
            env = self.gym.create_env(self.sim, env_lower, env_upper, num_per_row)
            self.envs.append(env)
            
            # Add robot
            spirob_pose = gymapi.Transform()
            spirob_pose.p = gymapi.Vec3(0.0, 0.0, 0.0)
            spirob_pose.r = gymapi.Quat(0, 0, 0, 1)
            
            spirob_handle = self.gym.create_actor(env, spirob_asset, spirob_pose, "spirob", i, 1)
            self.spirob_handles.append(spirob_handle)
            
            # Add object
            object_pose = gymapi.Transform()
            object_pose.p = gymapi.Vec3(0.0, 0.0, 0.05)
            object_pose.r = gymapi.Quat(0, 0, 0, 1)
            
            object_handle = self.gym.create_actor(env, self.object_asset, object_pose, "object", i, 2)
            self.object_handles.append(object_handle)
        
        # Get tensor handles for simulation data
        self._acquire_tensors()
        
        return self.sim

    def _acquire_tensors(self):
        """Get tensor handles for simulation data."""
        # Get handle for all tensors
        gym = self.gym
        sim = self.sim
        
        # Create buffers
        self.dof_state_tensor = gymtorch.wrap_tensor(
            gym.acquire_dof_state_tensor(sim))
        self.root_state_tensor = gymtorch.wrap_tensor(
            gym.acquire_actor_root_state_tensor(sim))
        
        # Prepare views into tensors
        self.dof_pos = self.dof_state_tensor[:, 0].view(self.num_envs, -1, 1)
        self.dof_vel = self.dof_state_tensor[:, 1].view(self.num_envs, -1, 1)
        
        # Handle for actor root states
        self.root_pos = self.root_state_tensor[:, 0:3].view(self.num_envs, -1, 3)
        self.root_rot = self.root_state_tensor[:, 3:7].view(self.num_envs, -1, 4)
        self.root_vel = self.root_state_tensor[:, 7:10].view(self.num_envs, -1, 3)
        self.root_ang_vel = self.root_state_tensor[:, 10:13].view(self.num_envs, -1, 3)
        
        # Reset buffers
        self.reset_buf = torch.zeros(self.num_envs, device=self.device, dtype=torch.int32)
        self.progress_buf = torch.zeros(self.num_envs, device=self.device, dtype=torch.int32)
        self.reward_buf = torch.zeros(self.num_envs, device=self.device, dtype=torch.float32)
        self.extras = {}

    def reset_idx(self, env_ids):
        """Reset environments by index."""
        num_resets = len(env_ids)
        
        # Randomize object positions for reset environments
        if num_resets > 0:
            # Reset progress and reward buffers
            self.progress_buf[env_ids] = 0
            self.reset_buf[env_ids] = 0
            
            # Reset DOF states for cable motors
            self.dof_pos[env_ids, :, 0] = torch.zeros((num_resets, self.num_actions), device=self.device)
            self.dof_vel[env_ids, :, 0] = torch.zeros((num_resets, self.num_actions), device=self.device)
            
            # Reset end effector position
            ee_indices = self.spirob_handles
            ee_pos = torch.tensor([0.0, 0.0, 0.15], device=self.device).repeat(num_resets, 1)
            ee_rot = torch.tensor([0.0, 0.0, 0.0, 1.0], device=self.device).repeat(num_resets, 1)
            
            # Randomize object positions
            if self.task_config.get("randomize_object", True):
                object_pos_x = torch.rand(num_resets, device=self.device) * 0.2 - 0.1
                object_pos_y = torch.rand(num_resets, device=self.device) * 0.2 - 0.1
                object_pos_z = torch.ones(num_resets, device=self.device) * 0.05
                object_pos = torch.stack([object_pos_x, object_pos_y, object_pos_z], dim=1)
            else:
                object_pos = torch.tensor([0.0, 0.0, 0.05], device=self.device).repeat(num_resets, 1)
            
            object_rot = torch.tensor([0.0, 0.0, 0.0, 1.0], device=self.device).repeat(num_resets, 1)
            
            # Set target positions
            self.object_pos_targets = object_pos.clone()
            
            # Apply to environment
            self._set_env_state(env_ids, 
                               ee_pos, ee_rot, torch.zeros_like(ee_pos), torch.zeros_like(ee_pos),
                               object_pos, object_rot, torch.zeros_like(object_pos), torch.zeros_like(object_pos))

    def _set_env_state(self, env_ids, ee_pos, ee_rot, ee_vel, ee_ang_vel, 
                      obj_pos, obj_rot, obj_vel, obj_ang_vel):
        """Set environment state for specified environments."""
        # Set end effector state
        self.root_pos[env_ids, 0] = ee_pos
        self.root_rot[env_ids, 0] = ee_rot
        self.root_vel[env_ids, 0] = ee_vel
        self.root_ang_vel[env_ids, 0] = ee_ang_vel
        
        # Set object state
        self.root_pos[env_ids, 1] = obj_pos
        self.root_rot[env_ids, 1] = obj_rot
        self.root_vel[env_ids, 1] = obj_vel
        self.root_ang_vel[env_ids, 1] = obj_ang_vel
        
        # Apply state to simulation
        self.gym.set_actor_root_state_tensor(self.sim, gymtorch.unwrap_tensor(self.root_state_tensor))
        self.gym.set_dof_state_tensor(self.sim, gymtorch.unwrap_tensor(self.dof_state_tensor))