import isaacgym
from isaacgym import gymapi
from isaacgym import gymtorch
from isaacgym.torch_utils import *

import math
import numpy as np
import torch
import random
import time
from typing import Dict, Any, Tuple

from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import CheckpointCallback
from stable_baselines3.common.torch_layers import BaseFeaturesExtractor
import torch.nn as nn

class SpiRobIsaacEnv:
    """
    SpiRob environment in Isaac Gym for reinforcement learning with
    3-cable parallel robot for object manipulation.
    """
    def __init__(self, 
                 task="pick",
                 num_envs=64,
                 sim_device="cuda:0",
                 headless=False,
                 episode_length=200):
        
        self.task = task
        self.num_envs = num_envs
        self.headless = headless
        self.episode_length = episode_length
        self.sim_device = sim_device
        self.device = torch.device(sim_device)
        self.steps = 0
        
        # Initialize gym
        self.gym = gymapi.acquire_gym()
        
        # Create simulator
        self.create_sim()
        
        # Create environments
        self.create_envs()
        
        # Prepare tensors for simulation data
        self.prepare_tensors()
        
        # Define observation and action spaces
        self.obs_dim = 18  # Same as MuJoCo env: [ee_pos(3), ee_vel(3), cable_lengths(3), cable_velocities(3), target_pos(3), target_vel(3)]
        self.action_dim = 3  # Control signals for 3 motors
        
        # Initialize step counters and other tracking variables
        self.reset_idx = torch.arange(self.num_envs, device=self.device)
        self.episode_lengths = torch.zeros(self.num_envs, device=self.device, dtype=torch.long)

    def create_sim(self):
        """Set up the Isaac Gym simulation."""
        # Create simulator parameters
        sim_params = gymapi.SimParams()
        
        # Set physics parameters
        sim_params.dt = 0.02
        sim_params.substeps = 2
        sim_params.up_axis = gymapi.UP_AXIS_Z
        sim_params.gravity = gymapi.Vec3(0.0, 0.0, -9.81)
        
        # Set collision parameters
        sim_params.physx.solver_type = 1
        sim_params.physx.num_position_iterations = 4
        sim_params.physx.num_velocity_iterations = 1
        sim_params.physx.contact_offset = 0.01
        sim_params.physx.rest_offset = 0.0
        
        # Create the simulation
        self.sim = self.gym.create_sim(0, 0, gymapi.SIM_PHYSX, sim_params)
        if self.sim is None:
            raise Exception("Failed to create simulation")
        
        # Create ground plane
        plane_params = gymapi.PlaneParams()
        plane_params.normal = gymapi.Vec3(0, 0, 1)
        plane_params.distance = 0
        plane_params.static_friction = 0.1
        plane_params.dynamic_friction = 0.1
        plane_params.restitution = 0.0
        self.gym.add_ground(self.sim, plane_params)
        
        # Create viewer
        if not self.headless:
            self.viewer = self.gym.create_viewer(self.sim, gymapi.CameraProperties())
            if self.viewer is None:
                raise Exception("Failed to create viewer")
            # Set viewer camera position
            cam_pos = gymapi.Vec3(1.5, 1.5, 1.5)
            cam_target = gymapi.Vec3(0.0, 0.0, 0.0)
            self.gym.viewer_camera_look_at(self.viewer, None, cam_pos, cam_target)

    def create_envs(self):
        """Create environments with SpiRob setups."""
        # Set the spacing between environments
        spacing = 1.5
        env_lower = gymapi.Vec3(-spacing, -spacing, 0.0)
        env_upper = gymapi.Vec3(spacing, spacing, spacing)
        
        # List to store environment handles
        self.envs = []
        self.ee_handles = []
        self.motor_handles = []
        self.cable_handles = []
        self.target_handles = []
        
        # Calculate max environments per row
        max_envs_per_row = int(np.sqrt(self.num_envs))
        
        # Create assets for the SpiRob components
        # Frame asset
        frame_asset = self._create_frame_asset()
        
        # End-effector asset (gripper)
        ee_asset = self._create_ee_asset()
        
        # Target object asset
        target_asset = self._create_target_asset()
        
        # Create environments
        for i in range(self.num_envs):
            # Calculate env position (in grid)
            row = i // max_envs_per_row
            col = i % max_envs_per_row
            env_pos = gymapi.Vec3(col * spacing, row * spacing, 0.0)
            
            # Create environment
            env_handle = self.gym.create_env(self.sim, env_lower, env_upper, max_envs_per_row)
            self.envs.append(env_handle)
            
            # Add frame to environment
            frame_pose = gymapi.Transform()
            frame_pose.p = gymapi.Vec3(0.0, 0.0, 0.0)
            frame_pose.r = gymapi.Quat(0, 0, 0, 1)
            frame_handle = self.gym.create_actor(env_handle, frame_asset, frame_pose, "frame", i, 0)
            
            # Add end-effector to environment
            ee_pose = gymapi.Transform()
            ee_pose.p = gymapi.Vec3(0.0, 0.0, 0.8)
            ee_pose.r = gymapi.Quat(0, 0, 0, 1)
            ee_handle = self.gym.create_actor(env_handle, ee_asset, ee_pose, "end_effector", i, 1)
            self.ee_handles.append(ee_handle)
            
            # Set end-effector properties (make it behave like a suspended object)
            props = self.gym.get_actor_rigid_body_properties(env_handle, ee_handle)
            props[0].mass = 0.1  # 100g end-effector
            self.gym.set_actor_rigid_body_properties(env_handle, ee_handle, props)
            
            # Add target object to environment
            target_pose = gymapi.Transform()
            if self.task == "pick":
                target_pose.p = gymapi.Vec3(0.1, 0.1, 0.03)  # On the ground
            else:  # catch task
                target_pose.p = gymapi.Vec3(0.1, 0.1, 1.0)  # In the air
            target_pose.r = gymapi.Quat(0, 0, 0, 1)
            target_handle = self.gym.create_actor(env_handle, target_asset, target_pose, "target", i, 2)
            self.target_handles.append(target_handle)
            
            # Set target object properties
            target_props = self.gym.get_actor_rigid_body_properties(env_handle, target_handle)
            target_props[0].mass = 0.05  # 50g object
            self.gym.set_actor_rigid_body_properties(env_handle, target_handle, target_props)
            
            # Create cables (as constraints)
            # Get motor and end-effector positions for cable attachment
            motor_positions = [
                gymapi.Vec3(0.5, 0.5, 1.5),   # Motor 1
                gymapi.Vec3(-0.5, 0.5, 1.5),  # Motor 2
                gymapi.Vec3(0, -0.5, 1.5)     # Motor 3
            ]
            
            cables = []
            for motor_idx, motor_pos in enumerate(motor_positions):
                # Create a cable constraint
                cable_props = gymapi.DistanceJointProperties()
                cable_props.rigid_stiffness = 5000.0  # Stiffness of the cable
                cable_props.rigid_damping = 100.0     # Damping of the cable
                cable_props.max_distance = 2.0        # Maximum cable length
                
                # Create the joint between motor position and end-effector
                cable = self.gym.create_distance_joint(
                    env_handle,
                    frame_handle, self.gym.get_rigid_body_index(frame_handle, motor_idx, gymapi.DOMAIN_ACTOR),
                    ee_handle, 0,
                    motor_pos, gymapi.Vec3(0, 0, 0)  # Local positions for joint
                )
                cables.append(cable)
            
            self.cable_handles.append(cables)
    
    def _create_frame_asset(self):
        """Create the frame asset with motor mounting points."""
        asset_options = gymapi.AssetOptions()
        asset_options.fix_base_link = True
        asset_options.density = 1000.0
        
        # Create a basic frame asset
        asset_root = "assets"  # A placeholder, we'll create the asset procedurally
        frame_asset = self.gym.create_box(self.sim, 0.02, 0.02, 1.5, asset_options)
        
        return frame_asset
    
    def _create_ee_asset(self):
        """Create the end-effector asset."""
        asset_options = gymapi.AssetOptions()
        asset_options.density = 1000.0
        
        # Create a spherical end-effector
        ee_asset = self.gym.create_sphere(self.sim, 0.05, asset_options)
        
        return ee_asset
    
    def _create_target_asset(self):
        """Create the target object asset."""
        asset_options = gymapi.AssetOptions()
        asset_options.density = 1000.0
        
        # Create a spherical target object
        target_asset = self.gym.create_sphere(self.sim, 0.03, asset_options)
        
        return target_asset

    def prepare_tensors(self):
        """Prepare tensors for vectorized simulation."""
        # Get total number of DOFs
        num_dofs = self.gym.get_sim_dof_count(self.sim)
        
        # Create buffers for data
        self.dof_state_tensor = gymtorch.wrap_tensor(
            self.gym.acquire_dof_state_tensor(self.sim)
        )
        self.rigid_body_states = gymtorch.wrap_tensor(
            self.gym.acquire_rigid_body_state_tensor(self.sim)
        )
        
        # Create actor root state tensor
        self.root_state_tensor = gymtorch.wrap_tensor(
            self.gym.acquire_actor_root_state_tensor(self.sim)
        )
        
        # Reshape tensors
        self.dof_state = self.dof_state_tensor.view(self.num_envs, -1, 2)
        self.root_positions = self.root_state_tensor[:, 0:3]
        self.root_orientations = self.root_state_tensor[:, 3:7]
        self.root_linvels = self.root_state_tensor[:, 7:10]
        self.root_angvels = self.root_state_tensor[:, 10:13]
        
        # Initialize cable length and velocity tensors
        self.cable_lengths = torch.zeros((self.num_envs, 3), device=self.device)
        self.cable_velocities = torch.zeros((self.num_envs, 3), device=self.device)
        
        # Create observation and reward tensors
        self.obs_buf = torch.zeros((self.num_envs, self.obs_dim), device=self.device)
        self.reward_buf = torch.zeros(self.num_envs, device=self.device)
        self.reset_buf = torch.ones(self.num_envs, device=self.device, dtype=torch.bool)

    def compute_observations(self):
        """Compute observations for all environments."""
        # Extract end-effector and target states from root state tensor
        ee_pos = self.root_positions.view(self.num_envs, -1, 13)[:, 1, 0:3]
        ee_vel = self.root_linvels.view(self.num_envs, -1, 6)[:, 1, 0:3]
        target_pos = self.root_positions.view(self.num_envs, -1, 13)[:, 2, 0:3]
        target_vel = self.root_linvels.view(self.num_envs, -1, 6)[:, 2, 0:3]
        
        # Compute cable lengths (distance between motors and end-effector)
        motor_positions = torch.tensor([
            [0.5, 0.5, 1.5],   # Motor 1
            [-0.5, 0.5, 1.5],  # Motor 2
            [0, -0.5, 1.5]     # Motor 3
        ], device=self.device)
        
        # Compute for all environments at once
        for i in range(3):
            motor_pos = motor_positions[i].unsqueeze(0).expand(self.num_envs, 3)
            self.cable_lengths[:, i] = torch.norm(ee_pos - motor_pos, dim=1)
        
        # Compute cable velocities (approximate using finite differences)
        if hasattr(self, 'prev_cable_lengths'):
            self.cable_velocities = (self.cable_lengths - self.prev_cable_lengths) / self.gym.get_sim_params(self.sim).dt
        self.prev_cable_lengths = self.cable_lengths.clone()
        
        # Combine all observations
        self.obs_buf = torch.cat([
            ee_pos, ee_vel,
            self.cable_lengths, self.cable_velocities,
            target_pos, target_vel
        ], dim=1)
        
        return self.obs_buf

    def compute_reward(self):
        """Compute rewards for all environments."""
        # Extract positions from observation
        ee_pos = self.obs_buf[:, 0:3]
        target_pos = self.obs_buf[:, 12:15]
        
        # Distance between end-effector and target
        distance = torch.norm(ee_pos - target_pos, dim=1)
        
        # Base reward is negative distance (closer is better)
        self.reward_buf = -distance
        
        # Check if the object is picked/caught
        close_to_target = distance < 0.08
        self.reward_buf = torch.where(close_to_target, self.reward_buf + 10.0, self.reward_buf)
        
        # Additional bonus for picking up the object (if it's lifted)
        if self.task == "pick":
            lifted = target_pos[:, 2] > 0.1
            # Bonus proportional to height
            height_bonus = 20.0 * target_pos[:, 2]
            self.reward_buf = torch.where(lifted & close_to_target, self.reward_buf + height_bonus, self.reward_buf)
        
        # Penalize if end-effector is outside the valid workspace
        workspace_x = (ee_pos[:, 0] > -0.4) & (ee_pos[:, 0] < 0.4)
        workspace_y = (ee_pos[:, 1] > -0.4) & (ee_pos[:, 1] < 0.4)
        workspace_z = (ee_pos[:, 2] > 0.1) & (ee_pos[:, 2] < 1.2)
        in_workspace = workspace_x & workspace_y & workspace_z
        self.reward_buf = torch.where(in_workspace, self.reward_buf, self.reward_buf - 5.0)
        
        return self.reward_buf
    
    def compute_reset(self):
        """Determine which environments should be reset."""
        # Extract positions from observation
        ee_pos = self.obs_buf[:, 0:3]
        target_pos = self.obs_buf[:, 12:15]
        distance = torch.norm(ee_pos - target_pos, dim=1)
        
        # Check workspace bounds
        workspace_x = (ee_pos[:, 0] > -0.4) & (ee_pos[:, 0] < 0.4)
        workspace_y = (ee_pos[:, 1] > -0.4) & (ee_pos[:, 1] < 0.4)
        workspace_z = (ee_pos[:, 2] > 0.1) & (ee_pos[:, 2] < 1.2)
        in_workspace = workspace_x & workspace_y & workspace_z
        
        # Reset if outside workspace
        self.reset_buf = ~in_workspace
        
        # Task-specific resets
        if self.task == "pick":
            # Success: object lifted above threshold
            success = target_pos[:, 2] > 0.3
            self.reset_buf = torch.logical_or(self.reset_buf, success)
        elif self.task == "catch":
            # Success: caught the object
            caught = (distance < 0.08) & (target_pos[:, 2] > 0.1)
            # Failed: object hit the ground
            ground_hit = target_pos[:, 2] < 0.03
            self.reset_buf = torch.logical_or(torch.logical_or(self.reset_buf, caught), ground_hit)
        
        # Reset based on episode length
        self.episode_lengths += 1
        episode_over = self.episode_lengths >= self.episode_length
        self.reset_buf = torch.logical_or(self.reset_buf, episode_over)
        
        return self.reset_buf
    
    def reset_idx(self, env_ids):
        """Reset specific environments."""
        if len(env_ids) == 0:
            return
        
        # Reset DOF states for selected environments
        actor_root_state = self.root_state_tensor.view(self.num_envs, -1, 13)
        
        # Reset end-effector position (center of workspace)
        actor_root_state[env_ids, 1, 0:3] = torch.tensor([0.0, 0.0, 0.8], device=self.device)
        actor_root_state[env_ids, 1, 3:7] = torch.tensor([1.0, 0.0, 0.0, 0.0], device=self.device)
        actor_root_state[env_ids, 1, 7:13] = 0.0  # Zero velocities
        
        # Reset target position based on task
        if self.task == "pick":
            # Random position on the ground
            x = torch.rand(len(env_ids), device=self.device) * 0.6 - 0.3
            y = torch.rand(len(env_ids), device=self.device) * 0.6 - 0.3
            z = torch.ones(len(env_ids), device=self.device) * 0.03  # Slightly above ground
            
            actor_root_state[env_ids, 2, 0] = x
            actor_root_state[env_ids, 2, 1] = y
            actor_root_state[env_ids, 2, 2] = z
            actor_root_state[env_ids, 2, 3:7] = torch.tensor([1.0, 0.0, 0.0, 0.0], device=self.device)
            actor_root_state[env_ids, 2, 7:13] = 0.0  # Zero velocities
        elif self.task == "catch":
            # Random position in the air with downward velocity
            x = torch.rand(len(env_ids), device=self.device) * 0.8 - 0.4
            y = torch.rand(len(env_ids), device=self.device) * 0.8 - 0.4
            z = torch.rand(len(env_ids), device=self.device) * 0.4 + 0.8  # Between 0.8 and 1.2
            
            actor_root_state[env_ids, 2, 0] = x
            actor_root_state[env_ids, 2, 1] = y
            actor_root_state[env_ids, 2, 2] = z
            actor_root_state[env_ids, 2, 3:7] = torch.tensor([1.0, 0.0, 0.0, 0.0], device=self.device)
            
            # Set falling velocity
            vx = torch.rand(len(env_ids), device=self.device) * 1.0 - 0.5
            vy = torch.rand(len(env_ids), device=self.device) * 1.0 - 0.5
            vz = torch.rand(len(env_ids), device=self.device) * -1.0 - 0.5  # Downward velocity
            
            actor_root_state[env_ids, 2, 7] = vx
            actor_root_state[env_ids, 2, 8] = vy
            actor_root_state[env_ids, 2, 9] = vz
            actor_root_state[env_ids, 2, 10:13] = 0.0  # Zero angular velocities
        
        # Apply the state updates
        self.gym.set_actor_root_state_tensor_indexed(
            self.sim,
            gymtorch.unwrap_tensor(self.root_state_tensor),
            gymtorch.unwrap_tensor(torch.tensor(env_ids, device=self.device, dtype=torch.int32)),
            len(env_ids)
        )
        
        # Reset episode length counter
        self.episode_lengths[env_ids] = 0
    
    def pre_physics_step(self, actions):
        """Apply actions before physics step."""
        # Actions are control signals for the 3 motors
        # We'll translate these into changes in cable lengths
        
        # Clamp actions
        actions = torch.clamp(actions, -1.0, 1.0)
        
        # Scale actions to cable length adjustments (motion control)
        # This simulates the stepper motors reeling in/out the cables
        actions_scaled = actions * 0.01  # 1cm max adjustment per step
        
        # Apply actions by moving constraints
        for i in range(self.num_envs):
            for j in range(3):
                # Calculate new cable length
                current_length = self.cable_lengths[i, j].item()
                adjustment = actions_scaled[i, j].item()
                
                # Enforce minimum and maximum cable lengths
                new_length = max(0.1, min(2.0, current_length + adjustment))
                
                # Update the cable constraint
                if len(self.cable_handles[i]) > j:
                    self.gym.set_distance_joint_distance(self.sim, self.envs[i], self.cable_handles[i][j], new_length)
    
    def post_physics_step(self):
        """Process after physics step."""
        self.progress_buf += 1
        
        # Compute observations, rewards, and resets
        self.compute_observations()
        self.compute_reward()
        self.compute_reset()
        
        # Reset environments if needed
        env_ids = self.reset_buf.nonzero(as_tuple=False).flatten()
        if len(env_ids) > 0:
            self.reset_idx(env_ids)
    
    def step(self, actions):
        """Step the physics, apply actions, and return observations."""
        # Convert actions to torch tensor if necessary
        if not isinstance(actions, torch.Tensor):
            actions = torch.tensor(actions, device=self.device)
        
        # Apply actions
        self.pre_physics_step(actions)
        
        # Step physics
        self.gym.simulate(self.sim)
        self.gym.fetch_results(self.sim, True)
        
        # Refresh tensors
        self.gym.refresh_actor_root_state_tensor(self.sim)
        self.gym.refresh_dof_state_tensor(self.sim)
        self.gym.refresh_rigid_body_state_tensor(self.sim)
        
        # Post-physics processing
        self.post_physics_step()
        
        # Update visualization if viewer exists
        if not self.headless:
            self.gym.step_graphics(self.sim)
            self.gym.draw_viewer(self.viewer, self.sim, True)
        
        # Return observation, reward, done, info
        return self.obs_buf, self.reward_buf, self.reset_buf, {}
    
    def reset(self):
        """Reset all environments."""
        # Reset all environments
        env_ids = torch.arange(self.num_envs, device=self.device)
        self.reset_idx(env_ids)
        
        # Step simulation to stabilize
        for _ in range(10):
            self.gym.simulate(self.sim)
            self.gym.fetch_results(self.sim, True)
        
        # Refresh tensors
        self.gym.refresh_actor_root_state_tensor(self.sim)
        self.gym.refresh_dof_state_tensor(self.sim)
        self.gym.refresh_rigid_body_state_tensor(self.sim)
        
        # Compute observations
        self.compute_observations()
        
        # Reset progress
        self.progress_buf = torch.zeros_like(self.progress_buf)
        self.episode_lengths = torch.zeros_like(self.episode_lengths)
        
        return self.obs_buf
    
    def close(self):
        """Clean up resources."""
        if not self.headless:
            self.gym.destroy_viewer(self.viewer)
        self.gym.destroy_sim(self.sim)


# Custom neural network policy for PPO
class SpiRobNetwork(BaseFeaturesExtractor):
    """Custom feature extractor for SpiRob RL."""
    
    def __init__(self, observation_space, features_dim=128):
        super(SpiRobNetwork, self).__init__(observation_space, features_dim)
        
        # Define neural network layers
        self.net = nn.Sequential(
            nn.Linear(observation_space.shape[0], 256),
            nn.ReLU(),
            nn.Linear(256, 256),
            nn.ReLU(),
            nn.Linear(256, features_dim),
            nn.ReLU(),
        )
    
    def forward(self, observations):
        return self.net(observations)


# Main training script
def train_spirob():
    """Main function to train the SpiRob using PPO in Isaac Gym."""
    # Create Isaac Gym environment
    env = SpiRobIsaacEnv(task="pick", num_envs=64, headless=False)
    
    # Define observation and action spaces for PPO
    from gym import spaces
    observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(env.obs_dim,))
    action_space = spaces.Box(low=-1.0, high=1.0, shape=(env.action_dim,))
    
    # Create policy with custom feature extractor
    policy_kwargs = dict(
        features_extractor_class=SpiRobNetwork,
        features_extractor_kwargs=dict(features_dim=128),
        net_arch=[dict(pi=[128, 128], vf=[128, 128])]
    )
    
    # Initialize PPO agent
    model = PPO(
        "MlpPolicy",
        env,
        policy_kwargs=policy_kwargs,
        verbose=1,
        n_steps=2048,
        batch_size=64,
        learning_rate=3e-4,
        gamma=0.99,
        ent_coef=0.01,
        vf_coef=0.5,
        max_grad_norm=0.5,
        use_sde=False,
        sde_sample_freq=-1,
        tensorboard_log="./spirob_tensorboard/",
        device=env.device
    )
    
    # Setup checkpoint callback
    checkpoint_callback = CheckpointCallback(
        save_freq=10000,
        save_path="./spirob_checkpoints/",
        name_prefix="spirob_model",
        save_replay_buffer=False,
        save_vecnormalize=False,
    )
    
    # Train the agent
    total_timesteps = 2000000
    model.learn(
        total_timesteps=total_timesteps,
        callback=checkpoint_callback,
        log_interval=10,
    )
    
    # Save final model
    model.save("spirob_final_model")
    
    # Close environment
    env.close()


if __name__ == "__main__":
    train_spirob()